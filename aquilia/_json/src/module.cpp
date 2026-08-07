// module.cpp -- nanobind glue for aquilia._json.
//
// The only Python-aware translation unit that is not itself an implementation
// unit, mirroring the split in _core and _dataengine: everything with logic in
// it (buffer, escape, numeric, encode, decode) is separately testable, and the
// escape scanner is testable without an interpreter at all.
//
// Kept deliberately thin. The binding layer's job is reference management and
// exception translation; it holds no encoding or parsing logic of its own.
//
// This is the *third* extension, not an addition to _core or _dataengine,
// because it has a dependency neither of those has (yyjson) and must be able to
// fail to build without taking them with it. An app whose JSON never leaves the
// stdlib path pays nothing for this code.

#include <nanobind/nanobind.h>

#include "buffer.hpp"
#include "decode.hpp"
#include "encode.hpp"

namespace nb = nanobind;

namespace {

/// Serialise an object to JSON bytes.
///
/// @param obj      The object graph.
/// @param default_fn  Fallback for unsupported types; None to disable.
/// @returns        A new `bytes`.
/// @throws EncodeError  The graph could not be serialised.
nb::object dumps(nb::handle obj, nb::handle default_fn) {
    // Pooled: the buffer's allocation is reused across calls on this thread, so
    // a server serialising a similar-sized response per request stops
    // allocating entirely after the first one.
    aq::json::PooledBuffer buf;

    PyObject* fn = default_fn.is_none() ? nullptr : default_fn.ptr();
    const aq::json::EncodeStatus rc = aq::json::encode(obj.ptr(), fn, *buf);
    if (rc != aq::json::EncodeStatus::Ok) {
        throw nb::python_error();
    }
    PyObject* out = PyBytes_FromStringAndSize(buf->data(), static_cast<Py_ssize_t>(buf->size()));
    if (!out) throw nb::python_error();
    return nb::steal(out);
}

/// Parse JSON from bytes or str.
///
/// @param data  `bytes`, `bytearray`, `memoryview`, or `str`.
/// @returns     The decoded object.
/// @throws DecodeError  Input was not well-formed JSON.
nb::object loads(nb::handle data) {
    PyObject* obj = data.ptr();

    const char* ptr = nullptr;
    Py_ssize_t len = 0;

    if (PyBytes_Check(obj)) {
        ptr = PyBytes_AS_STRING(obj);
        len = PyBytes_GET_SIZE(obj);
    } else if (PyUnicode_Check(obj)) {
        ptr = PyUnicode_AsUTF8AndSize(obj, &len);
        if (!ptr) throw nb::python_error();
    } else if (PyByteArray_Check(obj)) {
        // PyByteArray_AsString, not the AS_STRING macro: the macro dereferences
        // _PyByteArray_empty_string, which is private and does not link into an
        // extension module on macOS.
        ptr = PyByteArray_AsString(obj);
        if (!ptr) throw nb::python_error();
        len = PyByteArray_Size(obj);
    } else if (PyObject_CheckBuffer(obj)) {
        // memoryview and friends. The buffer is released before returning, so
        // the decoded objects never alias it.
        Py_buffer view{};
        if (PyObject_GetBuffer(obj, &view, PyBUF_SIMPLE) != 0) throw nb::python_error();
        PyObject* result = aq::json::decode(static_cast<const char*>(view.buf),
                                            static_cast<std::size_t>(view.len));
        PyBuffer_Release(&view);
        if (!result) throw nb::python_error();
        return nb::steal(result);
    } else {
        PyErr_Format(PyExc_TypeError, "the JSON object must be str, bytes or bytearray, not %s",
                     Py_TYPE(obj)->tp_name);
        throw nb::python_error();
    }

    PyObject* result = aq::json::decode(ptr, static_cast<std::size_t>(len));
    if (!result) throw nb::python_error();
    return nb::steal(result);
}

}  // namespace

NB_MODULE(_json, m) {
    m.doc() = "Aquilia native JSON engine: yyjson-backed decoding, direct-emit encoding.";

    // Errors surface as plain ValueError (malformed input) and TypeError
    // (unserialisable object), which is exactly what the stdlib codec raises.
    // aquilia/json.py translates them to JSONDecodeError/JSONEncodeError, both
    // of which subclass those same builtins -- so handlers written against
    // either the stdlib or this engine keep working unchanged. Defining a
    // parallel exception hierarchy here would add a translation step and buy
    // nothing.
    m.def("dumps", &dumps, nb::arg("obj").none(), nb::arg("default").none() = nb::none(),
          "Serialise an object to JSON bytes.");
    m.def("loads", &loads, nb::arg("data"), "Parse JSON from bytes or str.");

    // Boundary-cost probe, matching _dataengine's `noop`. The benchmark suite
    // measures the Python<->native call overhead against this so that a
    // per-call cost can be separated from the work itself.
    m.def("noop", []() {}, "Do nothing. Used to measure the Python<->native call cost.");
}
