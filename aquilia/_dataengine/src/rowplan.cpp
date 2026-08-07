#include "rowplan.hpp"

#include "convert.hpp"

namespace aq {

RowPlan::~RowPlan() {
    for (auto& op : ops_) {
        Py_XDECREF(op.key);
        Py_XDECREF(op.attr);
    }
    Py_XDECREF(model_cls_);
    Py_XDECREF(model_new_);
    Py_XDECREF(related_not_loaded_);
    Py_XDECREF(model_name_);
    Py_XDECREF(str_original_values_);
    Py_XDECREF(str_field_name_);
    Py_XDECREF(str_owner_model_name_);
}

void RowPlan::set_model(PyObject* model_cls, PyObject* related_not_loaded, PyObject* model_name) {
    Py_XSETREF(model_cls_, Py_NewRef(model_cls));
    Py_XSETREF(related_not_loaded_, Py_NewRef(related_not_loaded));
    Py_XSETREF(model_name_, Py_NewRef(model_name));
    // Resolved once. Looking __new__ up per row would reintroduce exactly the
    // per-row attribute dispatch this plan exists to remove.
    Py_XSETREF(model_new_, PyObject_GetAttrString(model_cls, "__new__"));
    Py_XSETREF(str_original_values_, PyUnicode_InternFromString("_original_values"));
    Py_XSETREF(str_field_name_, PyUnicode_InternFromString("field_name"));
    Py_XSETREF(str_owner_model_name_, PyUnicode_InternFromString("owner_model_name"));
}

void RowPlan::add(PyObject* key, PyObject* attr, TypeCode code, std::uint8_t flags) {
    ColumnOp op;
    op.key = Py_NewRef(key);
    op.attr = Py_NewRef(attr);
    op.code = code;
    op.flags = flags;
    ops_.push_back(op);
}

PyObject* RowPlan::execute(PyObject* rows) const {
    if (!PyList_CheckExact(rows)) return nullptr;

    const Py_ssize_t n = PyList_GET_SIZE(rows);
    PyObject* out = PyList_New(n);
    if (!out) return nullptr;

    // Cached so the FK-wrapping path does not rebuild the keyword dict per
    // value. RelatedNotLoaded takes field_name/owner_model_name keyword-only.
    PyObject* fk_kwargs = nullptr;

    for (Py_ssize_t i = 0; i < n; ++i) {
        PyObject* row = PyList_GET_ITEM(rows, i);  // borrowed
        // Row (the sqlite row type) subclasses dict, so PyDict_Check accepts
        // both it and the plain dicts other adapters return.
        if (!PyDict_Check(row)) {
            Py_XDECREF(fk_kwargs);
            Py_DECREF(out);
            return nullptr;  // no error set: caller falls back
        }

        // cls.__new__(cls) -- __init__ is bypassed, so pre_init/post_init do
        // NOT fire. They do not fire today either, and hydrating a 1,000-row
        // page must not start emitting 2,000 signal dispatches (04 section 3.1).
        PyObject* inst = PyObject_CallFunctionObjArgs(model_new_, model_cls_, nullptr);
        if (!inst) {
            Py_XDECREF(fk_kwargs);
            Py_DECREF(out);
            return nullptr;
        }

        PyObject* inst_dict = PyObject_GenericGetDict(inst, nullptr);
        if (!inst_dict) {
            Py_DECREF(inst);
            Py_XDECREF(fk_kwargs);
            Py_DECREF(out);
            return nullptr;
        }

        // The dirty-tracking snapshot. save() diffs against this to build
        // minimal UPDATEs, so it must hold the CONVERTED value and exactly the
        // attributes that were set -- no more, no fewer (04 section 3.2).
        PyObject* original = PyDict_New();
        if (!original) {
            Py_DECREF(inst_dict);
            Py_DECREF(inst);
            Py_XDECREF(fk_kwargs);
            Py_DECREF(out);
            return nullptr;
        }

        bool failed = false;
        for (const auto& op : ops_) {
            PyObject* raw = PyDict_GetItemWithError(row, op.key);
            if (!raw) {
                if (PyErr_Occurred()) {
                    failed = true;
                    break;
                }
                // The row does not carry this column. The plan was compiled
                // against this exact row shape, so a miss means the shape
                // changed mid-batch: abort rather than default the value to
                // None, which would be indistinguishable from a real SQL NULL.
                failed = true;
                break;
            }

            PyObject* value;
            if (raw == Py_None) {
                // NULL stays NULL, and a null FK is NOT wrapped.
                value = Py_NewRef(Py_None);
            } else {
                value = convert_hydrate(op.code, raw);
                if (!value) {
                    // A conversion error aborts the batch; Python re-runs it so
                    // the original exception and its diagnostics surface
                    // unchanged (04 section 7).
                    PyErr_Clear();
                    failed = true;
                    break;
                }

                if (op.flags & kFlagFkWrap) {
                    // A raw FK id is not a related instance. Wrapping it means
                    // attribute access raises RelatedNotLoadedFault with
                    // guidance rather than AttributeError on an int.
                    if (!fk_kwargs) {
                        fk_kwargs = PyDict_New();
                        if (!fk_kwargs) {
                            Py_DECREF(value);
                            failed = true;
                            break;
                        }
                    }
                    if (PyDict_SetItem(fk_kwargs, str_field_name_, op.attr) < 0 ||
                        PyDict_SetItem(fk_kwargs, str_owner_model_name_, model_name_) < 0) {
                        Py_DECREF(value);
                        failed = true;
                        break;
                    }
                    PyObject* args = PyTuple_Pack(1, value);
                    if (!args) {
                        Py_DECREF(value);
                        failed = true;
                        break;
                    }
                    PyObject* wrapped = PyObject_Call(related_not_loaded_, args, fk_kwargs);
                    Py_DECREF(args);
                    Py_DECREF(value);
                    if (!wrapped) {
                        failed = true;
                        break;
                    }
                    value = wrapped;
                }
            }

            // Writing the instance dict directly is exactly what Field.__set__
            // does; eligibility guarantees no field overrides it.
            const int rc1 = PyDict_SetItem(inst_dict, op.attr, value);
            const int rc2 = rc1 == 0 ? PyDict_SetItem(original, op.attr, value) : -1;
            Py_DECREF(value);
            if (rc1 < 0 || rc2 < 0) {
                failed = true;
                break;
            }
        }

        if (!failed) {
            if (PyObject_SetAttr(inst, str_original_values_, original) < 0) failed = true;
        }

        Py_DECREF(original);
        Py_DECREF(inst_dict);

        if (failed) {
            Py_DECREF(inst);
            Py_XDECREF(fk_kwargs);
            Py_DECREF(out);
            PyErr_Clear();  // fall back silently; Python reproduces any real error
            return nullptr;
        }

        PyList_SET_ITEM(out, i, inst);  // steals the reference
    }

    Py_XDECREF(fk_kwargs);
    return out;
}

}  // namespace aq
