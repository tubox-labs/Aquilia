// encode.cpp -- the direct emitter.
//
// Why not yyjson for encoding
// ---------------------------
// yyjson's mutable-document API would require building a yyjson_mut_val tree
// from the Python objects before writing a single byte: one allocation per node,
// a full traversal to build it, a second to serialise it, then teardown. For
// decoding yyjson wins outright (see decode.cpp) because it owns the parse. For
// encoding the source of truth is already a Python object graph, so the document
// is pure overhead -- this walks that graph once and appends bytes.
//
// Why an explicit work stack
// --------------------------
// A recursive encoder overflows the C stack on deeply nested input, and stack
// overflow is not a catchable error -- it is a crash. Since the input is
// attacker-controlled in any web framework, the traversal state lives in a
// heap-allocated stack instead, bounded by kMaxDepth. Deep input then produces a
// clean ValueError, which becomes a 400.

#include "encode.hpp"

#include <cstdint>
#include <vector>

#include "escape.hpp"
#include "numeric.hpp"

namespace aq {
namespace json {

namespace {

/// One level of in-progress container traversal.
///
/// `obj` holds a borrowed reference to the container being written; the caller's
/// root reference plus the container's own reference to its children keep
/// everything alive for the duration of the encode, so no incref happens here.
/// That matters: an incref/decref pair per container would be a measurable cost
/// on a large payload, and there is no window in which the graph can be mutated,
/// because encode() never calls back into arbitrary Python except through
/// `default_fn` -- which is handled separately, below.
struct Frame {
    PyObject* obj;        ///< The list/tuple/dict being written.
    Py_ssize_t index;     ///< Next child index (dicts: PyDict_Next position).
    bool is_mapping;      ///< Dict vs sequence.
    bool wrote_any;       ///< Whether a separator is needed before the next item.
};

/// True when `obj` is exactly `bool`. Checked before int, because in CPython
/// bool is a subclass of int and PyLong_Check would claim it.
inline bool is_exact_bool(PyObject* obj) noexcept { return obj == Py_True || obj == Py_False; }

/// Write a Python int, using the machine-word fast path where possible.
[[nodiscard]] bool write_pylong(PyObject* obj, Buffer& out) noexcept {
    // The common case: fits in a signed 64-bit word.
    int overflow = 0;
    const long long v = PyLong_AsLongLongAndOverflow(obj, &overflow);
    if (!overflow) {
        if (v == -1 && PyErr_Occurred()) return false;
        return write_int64(static_cast<std::int64_t>(v), out);
    }

    // Positive and beyond INT64_MAX: try unsigned before giving up. Hashes and
    // 64-bit ids land here often enough to be worth the branch.
    if (overflow > 0) {
        const unsigned long long uv = PyLong_AsUnsignedLongLong(obj);
        if (!PyErr_Occurred()) return write_uint64(static_cast<std::uint64_t>(uv), out);
        PyErr_Clear();
    }

    // Genuine bignum. JSON has no width limit, so this is legal -- fall back to
    // CPython's own decimal rendering.
    PyObject* s = PyObject_Str(obj);
    if (!s) return false;
    Py_ssize_t len = 0;
    const char* utf8 = PyUnicode_AsUTF8AndSize(s, &len);
    if (!utf8) {
        Py_DECREF(s);
        return false;
    }
    const bool ok = out.append(utf8, static_cast<std::size_t>(len));
    Py_DECREF(s);
    return ok;
}

/// Write a Python str.
[[nodiscard]] bool write_pyunicode(PyObject* obj, Buffer& out) noexcept {
    Py_ssize_t len = 0;
    // Returns the cached UTF-8 form, computing it once and storing it on the
    // object. No transcoding on repeat use -- which matters for dict keys, where
    // the same interned strings recur across every row of a response.
    const char* utf8 = PyUnicode_AsUTF8AndSize(obj, &len);
    if (!utf8) return false;
    return write_string(utf8, static_cast<std::size_t>(len), out);
}

/// Write a dict key. JSON requires string keys.
///
/// str is emitted directly. int/float/bool/None are stringified, matching
/// `json.dumps` with its default `skipkeys=False`; anything else is an error,
/// again matching stdlib.
[[nodiscard]] bool write_key(PyObject* key, Buffer& out) noexcept {
    if (PyUnicode_CheckExact(key) || PyUnicode_Check(key)) return write_pyunicode(key, out);

    if (is_exact_bool(key)) {
        return key == Py_True ? out.append_literal("\"true\"") : out.append_literal("\"false\"");
    }
    if (key == Py_None) return out.append_literal("\"null\"");
    if (PyLong_Check(key)) {
        if (!out.put('"')) return false;
        if (!write_pylong(key, out)) return false;
        return out.put('"');
    }
    if (PyFloat_Check(key)) {
        if (!out.put('"')) return false;
        if (!write_double(PyFloat_AS_DOUBLE(key), out)) return false;
        return out.put('"');
    }

    PyErr_Format(PyExc_TypeError, "keys must be str, int, float, bool or None, not %s",
                 Py_TYPE(key)->tp_name);
    return false;
}

}  // namespace

EncodeStatus encode(PyObject* obj, PyObject* default_fn, Buffer& out) noexcept {
    // Objects produced by default_fn are new references that must outlive the
    // frame referencing them. They are held here and released on exit, which is
    // also what makes it safe for the work stack to hold borrowed references.
    std::vector<PyObject*> owned;
    std::vector<Frame> stack;

    // Deep-but-not-recursive payloads are common (a list of rows of dicts), so
    // reserve enough for a typical shape without a realloc.
    stack.reserve(16);

    const auto cleanup = [&owned]() noexcept {
        for (PyObject* o : owned) Py_DECREF(o);
    };

    PyObject* current = obj;
    bool have_value = true;

    for (;;) {
        if (have_value) {
            have_value = false;
            PyObject* v = current;

            // ---- scalar dispatch, ordered by measured frequency -------------
            PyTypeObject* type = Py_TYPE(v);

            if (type == &PyUnicode_Type) {
                if (!write_pyunicode(v, out)) {
                    cleanup();
                    return EncodeStatus::Error;
                }
            } else if (v == Py_None) {
                if (!out.append_literal("null")) {
                    cleanup();
                    return EncodeStatus::Error;
                }
            } else if (is_exact_bool(v)) {
                // Before the int check: bool subclasses int in CPython.
                if (!(v == Py_True ? out.append_literal("true") : out.append_literal("false"))) {
                    cleanup();
                    return EncodeStatus::Error;
                }
            } else if (type == &PyLong_Type) {
                if (!write_pylong(v, out)) {
                    cleanup();
                    return EncodeStatus::Error;
                }
            } else if (type == &PyFloat_Type) {
                if (!write_double(PyFloat_AS_DOUBLE(v), out)) {
                    cleanup();
                    return EncodeStatus::Error;
                }
            } else if (type == &PyDict_Type || type == &PyList_Type || type == &PyTuple_Type) {
                // ---- container: push a frame -------------------------------
                if (stack.size() >= kMaxDepth) {
                    PyErr_SetString(PyExc_ValueError, "Maximum JSON nesting depth exceeded");
                    cleanup();
                    return EncodeStatus::Error;
                }
                const bool mapping = (type == &PyDict_Type);
                if (!out.put(mapping ? '{' : '[')) {
                    cleanup();
                    return EncodeStatus::Error;
                }
                stack.push_back(Frame{v, 0, mapping, false});
                continue;
            } else {
                // ---- slow path: subclasses, then default_fn ----------------
                // Subclasses of the builtins are handled here rather than in the
                // exact-type chain above so that the common case stays a pointer
                // comparison.
                if (PyUnicode_Check(v)) {
                    if (!write_pyunicode(v, out)) {
                        cleanup();
                        return EncodeStatus::Error;
                    }
                } else if (PyLong_Check(v)) {
                    if (!write_pylong(v, out)) {
                        cleanup();
                        return EncodeStatus::Error;
                    }
                } else if (PyFloat_Check(v)) {
                    if (!write_double(PyFloat_AS_DOUBLE(v), out)) {
                        cleanup();
                        return EncodeStatus::Error;
                    }
                } else if (PyDict_Check(v) || PyList_Check(v) || PyTuple_Check(v)) {
                    if (stack.size() >= kMaxDepth) {
                        PyErr_SetString(PyExc_ValueError, "Maximum JSON nesting depth exceeded");
                        cleanup();
                        return EncodeStatus::Error;
                    }
                    const bool mapping = PyDict_Check(v);
                    if (!out.put(mapping ? '{' : '[')) {
                        cleanup();
                        return EncodeStatus::Error;
                    }
                    stack.push_back(Frame{v, 0, mapping, false});
                    continue;
                } else if (default_fn) {
                    // default_fn may return anything, including another
                    // unsupported object. Encoding its result by looping would
                    // let a malicious hook recurse forever, so the result is
                    // encoded with default_fn disabled: one level of fallback,
                    // no more.
                    //
                    // PyObject_CallFunctionObjArgs rather than
                    // PyObject_CallOneArg: the latter is not exported to
                    // extension modules on all platforms (it fails to link on
                    // macOS), and the difference is not measurable here because
                    // this is already the slow path.
                    PyObject* replacement = PyObject_CallFunctionObjArgs(default_fn, v, nullptr);
                    if (!replacement) {
                        cleanup();
                        return EncodeStatus::Error;
                    }
                    owned.push_back(replacement);
                    const EncodeStatus rc = encode(replacement, nullptr, out);
                    if (rc != EncodeStatus::Ok) {
                        cleanup();
                        return rc;
                    }
                } else {
                    PyErr_Format(PyExc_TypeError, "Object of type %s is not JSON serializable",
                                 Py_TYPE(v)->tp_name);
                    cleanup();
                    return EncodeStatus::Error;
                }
            }
        }

        // ---- advance the innermost container ------------------------------
        if (stack.empty()) break;

        Frame& frame = stack.back();
        bool closed = false;

        if (frame.is_mapping) {
            PyObject* key = nullptr;
            PyObject* value = nullptr;
            // PyDict_Next's position is an opaque cursor, not an index; it must
            // be carried across iterations, which is exactly what frame.index
            // stores.
            if (PyDict_Next(frame.obj, &frame.index, &key, &value)) {
                if (frame.wrote_any && !out.put(',')) {
                    cleanup();
                    return EncodeStatus::Error;
                }
                frame.wrote_any = true;
                if (!write_key(key, out) || !out.put(':')) {
                    cleanup();
                    return EncodeStatus::Error;
                }
                current = value;
                have_value = true;
                continue;
            }
            closed = true;
        } else {
            const bool is_list = PyList_Check(frame.obj);
            const Py_ssize_t size = is_list ? PyList_GET_SIZE(frame.obj) : PyTuple_GET_SIZE(frame.obj);
            if (frame.index < size) {
                if (frame.wrote_any && !out.put(',')) {
                    cleanup();
                    return EncodeStatus::Error;
                }
                frame.wrote_any = true;
                current = is_list ? PyList_GET_ITEM(frame.obj, frame.index)
                                  : PyTuple_GET_ITEM(frame.obj, frame.index);
                ++frame.index;
                have_value = true;
                continue;
            }
            closed = true;
        }

        if (closed) {
            if (!out.put(frame.is_mapping ? '}' : ']')) {
                cleanup();
                return EncodeStatus::Error;
            }
            stack.pop_back();
        }
    }

    cleanup();
    return EncodeStatus::Ok;
}

}  // namespace json
}  // namespace aq
