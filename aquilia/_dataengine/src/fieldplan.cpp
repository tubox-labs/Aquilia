#include "fieldplan.hpp"

#include <cassert>
#include <cmath>

#include "convert.hpp"

namespace aq {
namespace {

// Outcome of one field's cast. kFallback means "this plan cannot decide with
// certainty" -- the caller re-runs the whole payload in Python rather than
// guessing, which is what keeps the two paths from diverging.
enum class Step { kOk, kFallback, kError };

// ASCII whitespace, matching what TextFacet's str.strip() would remove from an
// ASCII string. Non-ASCII strings are never inspected here (see cast_text).
inline bool is_ascii_space(Py_UCS4 c) {
    return c == ' ' || c == '\t' || c == '\n' || c == '\r' || c == '\v' || c == '\f';
}

// IntFacet.cast semantics, reproduced exactly (facets.py:1449, pinned row by row
// in 05 section 3.1). These are deliberate, counter-intuitive decisions and are
// precisely where a naive strtoll-style reimplementation would silently diverge:
//
//   True/False   rejected -- bool is an int subclass, so accepting it would let
//                True become 1
//   3.0          accepted -- no information is lost
//   3.9          REJECTED, not truncated. Truncation is silent data corruption:
//                a client sending {"quantity": 3.9} would get 3 persisted with
//                no indication anything was dropped.
//   NaN, +-inf   rejected
//   Decimal      same integral-value rule as float; deferred to Python here
//
// Every rejection returns kFallback so Python raises the real CastFault.
Step cast_int(PyObject* raw, PyObject** out) {
    // Checked before PyLong, because bool IS a PyLong subclass.
    if (PyBool_Check(raw)) return Step::kFallback;

    if (PyLong_CheckExact(raw)) {
        *out = Py_NewRef(raw);
        return Step::kOk;
    }

    if (PyFloat_CheckExact(raw)) {
        const double d = PyFloat_AS_DOUBLE(raw);
        // NaN fails self-comparison.
        if (d != d || std::isinf(d)) return Step::kFallback;
        double integral = 0.0;
        if (std::modf(d, &integral) != 0.0) return Step::kFallback;  // 3.9 -> reject
        PyObject* v = PyLong_FromDouble(d);
        if (!v) return Step::kError;
        *out = v;
        return Step::kOk;
    }

    if (PyUnicode_CheckExact(raw)) {
        // int(str) -- CPython's own parser, which rejects "3.9" for us.
        PyObject* v = PyNumber_Long(raw);
        if (!v) {
            PyErr_Clear();  // Python will raise the real CastFault
            return Step::kFallback;
        }
        *out = v;
        return Step::kOk;
    }

    // Decimal and everything else: let Python decide.
    return Step::kFallback;
}

// TextFacet.cast + the blank check from seal.
//
// trim defaults to True, so ignoring it would diverge on almost every contract.
// Rather than reimplement str.strip()'s Unicode whitespace rules, this only
// handles ASCII strings that need no trimming at all -- the overwhelmingly
// common case -- and defers everything else.
Step cast_text(PyObject* raw, std::uint8_t flags, PyObject** out) {
    if (!PyUnicode_CheckExact(raw)) {
        // int/float/bool coerce to str in Python; rarer, so defer.
        return Step::kFallback;
    }

    const Py_ssize_t len = PyUnicode_GET_LENGTH(raw);

    if (flags & kFieldTrim) {
        // Only ASCII can be checked cheaply and exactly against str.strip().
        if (!PyUnicode_IS_ASCII(raw)) return Step::kFallback;
        if (len > 0) {
            const Py_UCS4 first = PyUnicode_READ_CHAR(raw, 0);
            const Py_UCS4 last = PyUnicode_READ_CHAR(raw, len - 1);
            // Would strip: hand it to Python, which owns the trim.
            if (is_ascii_space(first) || is_ascii_space(last)) return Step::kFallback;
        }
    }

    // TextFacet.seal rejects "" unless allow_blank.
    if (len == 0 && !(flags & kFieldAllowBlank)) return Step::kFallback;

    *out = Py_NewRef(raw);
    return Step::kOk;
}

// FloatFacet.cast. allow_nan/allow_infinity default to False, so any non-finite
// result defers rather than encoding both flags.
Step cast_float(PyObject* raw, PyObject** out) {
    if (PyBool_Check(raw)) return Step::kFallback;

    if (PyFloat_CheckExact(raw)) {
        const double d = PyFloat_AS_DOUBLE(raw);
        if (d != d || std::isinf(d)) return Step::kFallback;
        *out = Py_NewRef(raw);
        return Step::kOk;
    }
    if (PyLong_CheckExact(raw) || PyUnicode_CheckExact(raw)) {
        PyObject* v = PyNumber_Float(raw);
        if (!v) {
            PyErr_Clear();
            return Step::kFallback;
        }
        const double d = PyFloat_AS_DOUBLE(v);
        if (d != d || std::isinf(d)) {
            Py_DECREF(v);
            return Step::kFallback;
        }
        *out = v;
        return Step::kOk;
    }
    return Step::kFallback;
}

Step cast_bool(PyObject* raw, PyObject** out) {
    if (PyBool_Check(raw)) {
        *out = Py_NewRef(raw);
        return Step::kOk;
    }
    // BoolFacet accepts a documented token set ("true"/"1"/"yes"/...). Encoding
    // it here would duplicate a table that lives in Python; defer.
    return Step::kFallback;
}

// Date/DateTime/Time from an ISO-8601 string, which is how they arrive in a JSON
// payload -- the common case, so it is worth handling rather than deferring.
//
// Safe because each facet's cast() is exactly `X.fromisoformat(value)` for a str
// input (facets.py), and fromisoformat is C in CPython at 18-25 ns -- cheaper
// than reimplementing ISO-8601 and risking timezone or fractional-second
// divergence. A ValueError means the same CastFault Python would raise, so it
// defers rather than reporting the error itself.
Step cast_iso(PyObject* raw, PyTypeObject* want, PyObject* fromisoformat, PyObject** out) {
    if (Py_IS_TYPE(raw, want)) {
        *out = Py_NewRef(raw);
        return Step::kOk;
    }
    if (!PyUnicode_CheckExact(raw)) return Step::kFallback;
    PyObject* v = PyObject_CallFunctionObjArgs(fromisoformat, raw, nullptr);
    if (!v) {
        PyErr_Clear();
        return Step::kFallback;
    }
    // Confirm the exact type rather than trusting the constructor, so a
    // subclass instance can never reach a facet expecting the base type.
    if (!Py_IS_TYPE(v, want)) {
        Py_DECREF(v);
        return Step::kFallback;
    }
    *out = v;
    return Step::kOk;
}

Step cast_uuid(PyObject* raw, PyObject** out) {
    if (Py_IS_TYPE(raw, ctors().uuid_type)) {
        *out = Py_NewRef(raw);
        return Step::kOk;
    }
    if (!PyUnicode_CheckExact(raw)) return Step::kFallback;
    PyObject* u = uuid_from_string(raw);
    if (u) {
        *out = u;
        return Step::kOk;
    }
    if (PyErr_Occurred()) PyErr_Clear();
    return Step::kFallback;
}

// Bounds, in the order IntFacet.seal applies them: min then max. The first
// violation is what Python reports, so order is observable.
// Returns kOk when the value passes, kFallback when it does not (Python raises
// the real error with the localised message).
Step check_bounds(const FieldOp& op, PyObject* value) {
    if (op.min_value) {
        const int lt = PyObject_RichCompareBool(value, op.min_value, Py_LT);
        if (lt < 0) return Step::kError;
        if (lt) return Step::kFallback;
    }
    if (op.max_value) {
        const int gt = PyObject_RichCompareBool(value, op.max_value, Py_GT);
        if (gt < 0) return Step::kError;
        if (gt) return Step::kFallback;
    }
    return Step::kOk;
}

Step check_lengths(const FieldOp& op, PyObject* value) {
    if (op.min_length < 0 && op.max_length < 0) return Step::kOk;
    // Only str reaches here; PyUnicode_GET_LENGTH counts code points, which is
    // exactly what len() returns.
    const Py_ssize_t len = PyUnicode_GET_LENGTH(value);
    if (op.min_length >= 0 && len < op.min_length) return Step::kFallback;
    if (op.max_length >= 0 && len > op.max_length) return Step::kFallback;
    return Step::kOk;
}

}  // namespace

FieldPlan::~FieldPlan() {
    for (auto& op : ops_) {
        Py_XDECREF(op.name);
        Py_XDECREF(op.default_value);
        Py_XDECREF(op.min_value);
        Py_XDECREF(op.max_value);
    }
}

void FieldPlan::add(PyObject* name, TypeCode code, std::uint8_t flags, PyObject* default_value,
                    PyObject* min_value, PyObject* max_value, Py_ssize_t min_length, Py_ssize_t max_length) {
    // kFieldHasDefault promises default_value is a real object. execute() stores
    // it with PyDict_SetItem, which segfaults on NULL rather than raising, so the
    // invariant is asserted here where the failure is still attributable. Note
    // that `default=None` is a real default and must arrive as Py_None, not null.
    assert(!(flags & kFieldHasDefault) || default_value != nullptr);
    FieldOp op;
    op.name = Py_NewRef(name);
    op.code = code;
    op.flags = flags;
    op.default_value = default_value ? Py_NewRef(default_value) : nullptr;
    op.min_value = min_value ? Py_NewRef(min_value) : nullptr;
    op.max_value = max_value ? Py_NewRef(max_value) : nullptr;
    op.min_length = min_length;
    op.max_length = max_length;
    ops_.push_back(op);
}

int FieldPlan::execute(PyObject* payload, PyObject** validated) const {
    // Exactly dict, not a subclass: MultiDict and FormData need the alternate
    // key handling ("field[]", flat-list extraction) that lives in Python.
    if (!PyDict_CheckExact(payload)) return 0;

    PyObject* out = PyDict_New();
    if (!out) return -1;

    for (const auto& op : ops_) {
        // Interned key -> the dict lookup hits its pointer-equality fast path.
        PyObject* raw = PyDict_GetItemWithError(payload, op.name);
        if (!raw) {
            if (PyErr_Occurred()) {
                Py_DECREF(out);
                return -1;
            }
            // Missing. This order is load-bearing (05 section 3.4): default is
            // consulted BEFORE required, so a field that is both required and
            // defaulted uses the default rather than erroring.
            if (op.flags & kFieldHasDefault) {
                if (PyDict_SetItem(out, op.name, op.default_value) < 0) {
                    Py_DECREF(out);
                    return -1;
                }
                continue;
            }
            if (op.flags & kFieldRequired) {
                Py_DECREF(out);
                return 0;  // Python produces the "required" error
            }
            if (op.flags & kFieldAllowNull) {
                if (PyDict_SetItem(out, op.name, Py_None) < 0) {
                    Py_DECREF(out);
                    return -1;
                }
                continue;
            }
            continue;  // absent and optional: skipped silently
        }

        // An explicit None is NOT interchangeable with a missing key
        // (05 section 3.5) -- they follow different resolution paths.
        if (raw == Py_None) {
            if (op.flags & kFieldAllowNull) {
                if (PyDict_SetItem(out, op.name, Py_None) < 0) {
                    Py_DECREF(out);
                    return -1;
                }
                continue;
            }
            Py_DECREF(out);
            return 0;  // Python produces the "not_null" error
        }

        PyObject* value = nullptr;
        Step step;
        switch (op.code) {
            case TypeCode::Int:
                step = cast_int(raw, &value);
                break;
            case TypeCode::Str:
                step = cast_text(raw, op.flags, &value);
                break;
            case TypeCode::Float:
                step = cast_float(raw, &value);
                break;
            case TypeCode::Bool:
                step = cast_bool(raw, &value);
                break;
            case TypeCode::Uuid:
                step = cast_uuid(raw, &value);
                break;
            case TypeCode::Date:
                step = cast_iso(raw, ctors().date_type, ctors().date_fromisoformat, &value);
                break;
            case TypeCode::DateTime:
                step = cast_iso(raw, ctors().datetime_type, ctors().datetime_fromisoformat, &value);
                break;
            case TypeCode::Time:
                step = cast_iso(raw, ctors().time_type, ctors().time_fromisoformat, &value);
                break;
            default:
                step = Step::kFallback;
                break;
        }

        if (step == Step::kOk) {
            step = (op.code == TypeCode::Str) ? check_lengths(op, value) : check_bounds(op, value);
        }

        // Single release path for `value`. An earlier version decref'd it inside
        // the constraint branch *and* again here, which double-freed whenever a
        // bounds comparison failed -- a segfault, caught by the mail config
        // tests rather than by anything in tests/dataengine.
        if (step != Step::kOk) {
            Py_XDECREF(value);
            Py_DECREF(out);
            return step == Step::kError ? -1 : 0;
        }

        const int rc = PyDict_SetItem(out, op.name, value);
        Py_DECREF(value);
        if (rc < 0) {
            Py_DECREF(out);
            return -1;
        }
    }

    *validated = out;
    return 1;
}

}  // namespace aq
