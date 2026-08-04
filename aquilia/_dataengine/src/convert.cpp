#include "convert.hpp"

#include <cstdint>
#include <string_view>

#include "uuid_parse.hpp"

namespace aq {
namespace {

Constructors g_ctors;

// Fetch `module.attr` as a new reference, or nullptr with an error set.
PyObject* import_from(const char* module, const char* attr) {
    PyObject* m = PyImport_ImportModule(module);
    if (!m) return nullptr;
    PyObject* o = PyObject_GetAttrString(m, attr);
    Py_DECREF(m);
    return o;
}

}  // namespace

const Constructors& ctors() { return g_ctors; }

bool init_constructors() {
    if (g_ctors.ready) return true;

    // datetime.date / datetime / time -- fromisoformat is C in CPython and costs
    // 18-25 ns, so calling back into it is correct. Reimplementing ISO-8601
    // parsing natively would risk timezone, fractional-second, and "Z"-suffix
    // divergence for a gain measurement says is near zero (03 section 5).
    PyObject* date_cls = import_from("datetime", "date");
    if (!date_cls) return false;
    g_ctors.date_fromisoformat = PyObject_GetAttrString(date_cls, "fromisoformat");
    g_ctors.date_type = reinterpret_cast<PyTypeObject*>(date_cls);  // keeps the ref
    if (!g_ctors.date_fromisoformat) return false;

    PyObject* dt_cls = import_from("datetime", "datetime");
    if (!dt_cls) return false;
    g_ctors.datetime_fromisoformat = PyObject_GetAttrString(dt_cls, "fromisoformat");
    g_ctors.datetime_type = reinterpret_cast<PyTypeObject*>(dt_cls);  // keeps the ref
    if (!g_ctors.datetime_fromisoformat) return false;

    PyObject* time_cls = import_from("datetime", "time");
    if (!time_cls) return false;
    g_ctors.time_fromisoformat = PyObject_GetAttrString(time_cls, "fromisoformat");
    g_ctors.time_type = reinterpret_cast<PyTypeObject*>(time_cls);  // keeps the ref
    if (!g_ctors.time_fromisoformat) return false;

    // _decimal is C; Decimal(str) is 44.7 ns, at parity with one crossing.
    g_ctors.decimal_type = import_from("decimal", "Decimal");
    if (!g_ctors.decimal_type) return false;

    g_ctors.json_loads = import_from("json", "loads");
    if (!g_ctors.json_loads) return false;

    PyObject* uuid_cls = import_from("uuid", "UUID");
    if (!uuid_cls) return false;
    if (!PyType_Check(uuid_cls)) {
        Py_DECREF(uuid_cls);
        PyErr_SetString(PyExc_TypeError, "uuid.UUID is not a type");
        return false;
    }
    g_ctors.uuid_type = reinterpret_cast<PyTypeObject*>(uuid_cls);  // keeps the ref

    PyObject* safe_enum = import_from("uuid", "SafeUUID");
    if (!safe_enum) return false;
    g_ctors.safe_uuid_unknown = PyObject_GetAttrString(safe_enum, "unknown");
    Py_DECREF(safe_enum);
    if (!g_ctors.safe_uuid_unknown) return false;

    g_ctors.str_int = PyUnicode_InternFromString("int");
    if (!g_ctors.str_int) return false;
    g_ctors.str_is_safe = PyUnicode_InternFromString("is_safe");
    if (!g_ctors.str_is_safe) return false;

    // Accessing a __slots__ attribute on the *class* yields its
    // member_descriptor. Caching the two descriptors lets uuid_from_string call
    // tp_descr_set directly, skipping the attribute-name resolution that
    // PyObject_GenericSetAttr would repeat on every parse.
    g_ctors.uuid_int_descr = PyObject_GetAttr(reinterpret_cast<PyObject*>(g_ctors.uuid_type), g_ctors.str_int);
    if (!g_ctors.uuid_int_descr) return false;
    g_ctors.uuid_is_safe_descr =
        PyObject_GetAttr(reinterpret_cast<PyObject*>(g_ctors.uuid_type), g_ctors.str_is_safe);
    if (!g_ctors.uuid_is_safe_descr) return false;

    // Both must actually be data descriptors, or the direct-set path below is
    // invalid. If uuid's internals ever change shape, fail loudly at import
    // rather than silently producing half-initialised UUIDs.
    if (!Py_TYPE(g_ctors.uuid_int_descr)->tp_descr_set || !Py_TYPE(g_ctors.uuid_is_safe_descr)->tp_descr_set) {
        PyErr_SetString(PyExc_TypeError, "uuid.UUID slots are not settable data descriptors");
        return false;
    }

    g_ctors.ready = true;
    return true;
}

PyObject* uuid_from_string(PyObject* s) {
    Py_ssize_t len = 0;
    const char* buf = PyUnicode_AsUTF8AndSize(s, &len);
    if (!buf) return nullptr;  // not a str, or not encodable -- error is set

    char hex[kUuidHexBufSize];
    if (!normalise_uuid_hex(std::string_view(buf, static_cast<std::size_t>(len)), hex)) {
        // Outside the accepted grammar. NOT an error: CPython accepts several
        // forms this parser deliberately refuses (underscores, signs,
        // whitespace), so the caller must defer to uuid.UUID rather than treat
        // this as invalid input.
        return nullptr;
    }

    // uuid.UUID stores a single 128-bit int. Build it directly rather than
    // calling UUID(hex=...), whose __init__ is the pure-Python cost being
    // avoided: three str.replace calls plus strip/count/len per parse.
    //
    // PyLong_FromString rather than _PyLong_FromByteArray: the latter is
    // declared in cpython/longobject.h but is not exported by every CPython
    // build (this one included), and an extension that fails to link on some
    // interpreters is worse than one that spends a few ns more. Feeding it the
    // normalised buffer is safe precisely because normalise_uuid_hex has
    // already guaranteed 32 pure hex digits -- PyLong_FromString(base=16) would
    // otherwise accept underscores, signs, and whitespace of its own accord.
    PyObject* as_int = PyLong_FromString(hex, nullptr, 16);
    if (!as_int) return nullptr;

    PyObject* u = g_ctors.uuid_type->tp_alloc(g_ctors.uuid_type, 0);
    if (!u) {
        Py_DECREF(as_int);
        return nullptr;
    }

    // UUID declares __slots__ = ('int', 'is_safe', '__weakref__') and a
    // __setattr__ that raises ("UUID objects are immutable"), so the slots are
    // written through the member descriptors' tp_descr_set -- the same store
    // object.__setattr__ performs, and what UUID.__init__ itself ends up doing,
    // minus the per-call attribute-name resolution.
    if (Py_TYPE(g_ctors.uuid_int_descr)->tp_descr_set(g_ctors.uuid_int_descr, u, as_int) < 0) {
        Py_DECREF(as_int);
        Py_DECREF(u);
        return nullptr;
    }
    Py_DECREF(as_int);

    if (Py_TYPE(g_ctors.uuid_is_safe_descr)
            ->tp_descr_set(g_ctors.uuid_is_safe_descr, u, g_ctors.safe_uuid_unknown) < 0) {
        Py_DECREF(u);
        return nullptr;
    }
    return u;
}

namespace {

// True for a str that is empty or all-whitespace, which every date/decimal/uuid
// to_python maps to None. Only ASCII is decided here; a non-ASCII string defers,
// because str.strip() follows Unicode whitespace rules this does not model.
// Returns: 1 = blank, 0 = not blank, -1 = cannot decide.
int ascii_blank(PyObject* s) {
    if (!PyUnicode_IS_ASCII(s)) return -1;
    const Py_ssize_t n = PyUnicode_GET_LENGTH(s);
    for (Py_ssize_t i = 0; i < n; ++i) {
        const Py_UCS4 c = PyUnicode_READ_CHAR(s, i);
        if (c != ' ' && c != '\t' && c != '\n' && c != '\r' && c != '\v' && c != '\f') return 0;
    }
    return 1;
}

}  // namespace

PyObject* convert_hydrate(TypeCode code, PyObject* raw) {
    switch (code) {
        case TypeCode::Str:
            // CharField and friends inherit the base to_python, a passthrough.
            return Py_NewRef(raw);

        case TypeCode::Int:
            if (PyLong_CheckExact(raw)) return Py_NewRef(raw);
            return Py_NewRef(raw);  // base to_python is a passthrough

        case TypeCode::Float:
            if (PyFloat_CheckExact(raw)) return Py_NewRef(raw);
            return Py_NewRef(raw);  // base to_python is a passthrough

        case TypeCode::Bool:
            // BooleanField.to_python: bool(value), by truthiness.
            return PyBool_FromLong(PyObject_IsTrue(raw));

        case TypeCode::Date:
        case TypeCode::DateTime:
        case TypeCode::Time: {
            PyTypeObject* want = code == TypeCode::Date     ? g_ctors.date_type
                                 : code == TypeCode::DateTime ? g_ctors.datetime_type
                                                              : g_ctors.time_type;
            // DateField accepts any datetime.date instance as-is, and datetime
            // subclasses date, so isinstance is correct here -- unlike the
            // contracts path, which needs the exact type.
            if (PyObject_TypeCheck(raw, want)) return Py_NewRef(raw);
            if (!PyUnicode_CheckExact(raw)) return Py_NewRef(raw);  // passthrough
            const int blank = ascii_blank(raw);
            if (blank < 0) return nullptr;               // cannot decide -> fall back
            if (blank) return Py_NewRef(Py_None);        // blank string -> None
            PyObject* fn = code == TypeCode::Date       ? g_ctors.date_fromisoformat
                           : code == TypeCode::DateTime ? g_ctors.datetime_fromisoformat
                                                        : g_ctors.time_fromisoformat;
            return PyObject_CallFunctionObjArgs(fn, raw, nullptr);
        }

        case TypeCode::Decimal: {
            if (PyUnicode_CheckExact(raw)) {
                const int blank = ascii_blank(raw);
                if (blank < 0) return nullptr;
                if (blank) return Py_NewRef(Py_None);
            }
            // DecimalField.to_python is Decimal(str(value)); the str() matters
            // for float input, where Decimal(float) would keep binary error.
            PyObject* as_str = PyObject_Str(raw);
            if (!as_str) return nullptr;
            PyObject* v = PyObject_CallFunctionObjArgs(g_ctors.decimal_type, as_str, nullptr);
            Py_DECREF(as_str);
            return v;
        }

        case TypeCode::Uuid: {
            if (Py_IS_TYPE(raw, g_ctors.uuid_type)) return Py_NewRef(raw);
            if (!PyUnicode_CheckExact(raw)) {
                // to_python does uuid.UUID(str(value)); defer the odd shapes.
                return nullptr;
            }
            const int blank = ascii_blank(raw);
            if (blank < 0) return nullptr;
            if (blank) return Py_NewRef(Py_None);
            PyObject* u = uuid_from_string(raw);
            if (u) return u;
            if (PyErr_Occurred()) PyErr_Clear();
            return PyObject_CallFunctionObjArgs(reinterpret_cast<PyObject*>(g_ctors.uuid_type), raw, nullptr);
        }

        case TypeCode::Json: {
            if (!PyUnicode_Check(raw) && !PyBytes_Check(raw)) {
                // Already-decoded values (PostgreSQL JSONB) pass through.
                return Py_NewRef(raw);
            }
            PyObject* v = PyObject_CallFunctionObjArgs(g_ctors.json_loads, raw, nullptr);
            if (v) return v;
            // JSONField deliberately returns an unparseable string AS-IS rather
            // than raising, so an invalid value is not an error here.
            PyErr_Clear();
            return Py_NewRef(raw);
        }

        case TypeCode::Bytes:
            return Py_NewRef(raw);

        default:
            return nullptr;  // fall back
    }
}

PyObject* convert(TypeCode code, PyObject* raw) {
    switch (code) {
        case TypeCode::Passthrough:
            return Py_NewRef(raw);

        case TypeCode::Str:
            if (PyUnicode_CheckExact(raw)) return Py_NewRef(raw);
            return PyObject_Str(raw);

        case TypeCode::Int:
            if (PyLong_CheckExact(raw)) return Py_NewRef(raw);
            // PyNumber_Long is CPython's own int() and handles str, bytes, and
            // __int__ alike at ~27 ns. Note this is the *hydration* path, where
            // the DB is the source of truth; IntFacet's much stricter cast
            // semantics live in fieldplan.cpp.
            return PyNumber_Long(raw);

        case TypeCode::Float:
            if (PyFloat_CheckExact(raw)) return Py_NewRef(raw);
            return PyNumber_Float(raw);

        case TypeCode::Bool:
            return PyBool_FromLong(PyObject_IsTrue(raw));

        case TypeCode::Date:
            if (!PyUnicode_Check(raw)) return Py_NewRef(raw);
            return PyObject_CallFunctionObjArgs(g_ctors.date_fromisoformat, raw, nullptr);

        case TypeCode::DateTime:
            if (!PyUnicode_Check(raw)) return Py_NewRef(raw);
            return PyObject_CallFunctionObjArgs(g_ctors.datetime_fromisoformat, raw, nullptr);

        case TypeCode::Time:
            if (!PyUnicode_Check(raw)) return Py_NewRef(raw);
            return PyObject_CallFunctionObjArgs(g_ctors.time_fromisoformat, raw, nullptr);

        case TypeCode::Decimal:
            return PyObject_CallFunctionObjArgs(g_ctors.decimal_type, raw, nullptr);

        case TypeCode::Uuid: {
            if (!PyUnicode_Check(raw)) return Py_NewRef(raw);
            PyObject* u = uuid_from_string(raw);
            if (u) return u;
            if (PyErr_Occurred()) return nullptr;
            // Grammar this parser refuses but CPython may accept. Defer to
            // uuid.UUID so semantics stay identical.
            return PyObject_CallFunctionObjArgs(reinterpret_cast<PyObject*>(g_ctors.uuid_type), raw, nullptr);
        }

        case TypeCode::Json:
            if (!PyUnicode_Check(raw) && !PyBytes_Check(raw)) return Py_NewRef(raw);
            return PyObject_CallFunctionObjArgs(g_ctors.json_loads, raw, nullptr);

        case TypeCode::Bytes:
            if (PyBytes_CheckExact(raw)) return Py_NewRef(raw);
            if (PyUnicode_Check(raw)) {
                Py_ssize_t n = 0;
                const char* b = PyUnicode_AsUTF8AndSize(raw, &n);
                if (!b) return nullptr;
                return PyBytes_FromStringAndSize(b, n);
            }
            return Py_NewRef(raw);

        case TypeCode::Unsupported:
        default:
            // Unreachable: an Unsupported code makes the whole plan ineligible
            // at compile time, so no plan containing one ever executes.
            PyErr_SetString(PyExc_SystemError, "aquilia._dataengine: unsupported type code executed");
            return nullptr;
    }
}

}  // namespace aq
