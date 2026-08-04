// decode.cpp -- yyjson-backed parsing into Python objects.
//
// Two decisions worth recording:
//
// 1. **yyjson owns the parse.** Its immutable reader allocates the entire
//    document from a single arena, so a 100KB payload costs one allocation
//    rather than one per node. CPython's parser cannot match that, and unlike
//    the encode direction there is no Python object graph already in hand to
//    make the intermediate document redundant.
//
// 2. **The tree walk is iterative.** Same reason as the encoder: nesting depth
//    is attacker-controlled, and a recursive walk turns a hostile payload into a
//    stack overflow, which is a crash rather than a catchable error. yyjson
//    itself is already non-recursive; this keeps the Python-building half
//    non-recursive too.
//
// Duplicate keys resolve last-wins, matching both `json.loads` and every other
// mainstream parser. Rejecting them would be defensible but would break real
// payloads that stdlib accepts today.

#include "decode.hpp"

#include <cstring>
#include <vector>

#include "yyjson.h"

namespace aq {
namespace json {

namespace {

/// Matches the encoder's limit so a payload this framework produced is always
/// one it can read back.
constexpr std::size_t kMaxDepth = 1024;

/// A container being filled, plus the yyjson cursor for its remaining children.
struct Frame {
    PyObject* container;  ///< Strong reference: the dict or list being built.
    yyjson_val* val;      ///< The yyjson container it came from.
    yyjson_obj_iter obj_iter;
    yyjson_arr_iter arr_iter;
    bool is_object;
    /// The key this container is stored under in its *parent*, when the parent
    /// is an object.
    ///
    /// This has to live in the frame rather than in a single `pending_key`
    /// variable: while iterating a nested object we overwrite the current key on
    /// every child, so by the time the nested container is finished the parent's
    /// key would have been clobbered. Storing it per frame is what makes
    /// `{"a": {"b": 1}, "c": 2}` come out right instead of losing "a".
    const char* parent_key;
    std::size_t parent_key_len;
};

/// Convert one non-container yyjson value to a new Python reference.
[[nodiscard]] PyObject* scalar_to_python(yyjson_val* val) noexcept {
    switch (yyjson_get_type(val)) {
        case YYJSON_TYPE_NULL:
            Py_RETURN_NONE;
        case YYJSON_TYPE_BOOL:
            if (yyjson_get_bool(val)) Py_RETURN_TRUE;
            Py_RETURN_FALSE;
        case YYJSON_TYPE_RAW: {
            // An integer too large for uint64/int64. Read with
            // YYJSON_READ_BIGNUM_AS_RAW so the original digits survive; Python
            // ints are arbitrary precision, so parsing them as a double (which
            // is what yyjson would otherwise do) would silently lose precision.
            // json.loads returns the exact value here, and matching that is the
            // difference between a correct id and a corrupted one.
            const char* s = yyjson_get_raw(val);
            const std::size_t n = yyjson_get_len(val);

            // The raw span points into the document and is NOT NUL-terminated,
            // while PyLong_FromString requires termination and would otherwise
            // read into the following token. Copy into a bounded scratch buffer;
            // anything longer than this is not a number any caller meant.
            constexpr std::size_t kMaxRawDigits = 1024;
            if (n == 0 || n >= kMaxRawDigits) {
                PyErr_SetString(PyExc_ValueError, "number too long to decode");
                return nullptr;
            }
            char scratch[kMaxRawDigits];
            std::memcpy(scratch, s, n);
            scratch[n] = '\0';

            PyObject* result = PyLong_FromString(scratch, nullptr, 10);
            if (result) return result;
            // Not an integer after all (a float carrying more digits than a
            // double can represent). Fall back to the float, as stdlib does.
            PyErr_Clear();
            PyObject* text = PyUnicode_FromStringAndSize(scratch, static_cast<Py_ssize_t>(n));
            if (!text) return nullptr;
            PyObject* as_float = PyFloat_FromString(text);
            Py_DECREF(text);
            return as_float;
        }
        case YYJSON_TYPE_NUM:
            switch (yyjson_get_subtype(val)) {
                case YYJSON_SUBTYPE_UINT:
                    return PyLong_FromUnsignedLongLong(yyjson_get_uint(val));
                case YYJSON_SUBTYPE_SINT:
                    return PyLong_FromLongLong(yyjson_get_sint(val));
                default:
                    return PyFloat_FromDouble(yyjson_get_real(val));
            }
        case YYJSON_TYPE_STR: {
            const char* s = yyjson_get_str(val);
            const std::size_t n = yyjson_get_len(val);
            // yyjson has already validated the UTF-8, so the strict decoder is
            // the right one: it will not silently mask a parser bug.
            return PyUnicode_DecodeUTF8(s, static_cast<Py_ssize_t>(n), "strict");
        }
        default:
            PyErr_SetString(PyExc_ValueError, "unsupported JSON value");
            return nullptr;
    }
}

}  // namespace

PyObject* decode(const char* data, std::size_t len) noexcept {
    if (len == 0) {
        PyErr_SetString(PyExc_ValueError, "Expecting value: empty input");
        return nullptr;
    }

    yyjson_read_err err{};
    // YYJSON_READ_NOFLAG for in-situ: the input buffer belongs to the caller (it
    // is the bytes object's storage, or a memoryview over it), so the mutating
    // in-situ mode is not permitted here.
    //
    // BIGNUM_AS_RAW keeps integers that exceed uint64/int64 as their original
    // digits instead of coercing them to a double. Python ints are arbitrary
    // precision, so silently rounding a 30-digit id to 1.2345678901234568e+29 --
    // which is what the default does -- would be data corruption that json.loads
    // does not commit. scalar_to_python turns the raw digits back into an exact
    // int.
    yyjson_doc* doc = yyjson_read_opts(const_cast<char*>(data), len, YYJSON_READ_BIGNUM_AS_RAW,
                                       nullptr, &err);
    if (!doc) {
        // Message shape mirrors json.JSONDecodeError closely enough that
        // existing log-scraping and error handling keep working.
        PyErr_Format(PyExc_ValueError, "%s: line 1 column %zu (char %zu)", err.msg, err.pos + 1, err.pos);
        return nullptr;
    }

    yyjson_val* root = yyjson_doc_get_root(doc);
    if (!root) {
        yyjson_doc_free(doc);
        PyErr_SetString(PyExc_ValueError, "Expecting value");
        return nullptr;
    }

    std::vector<Frame> stack;
    stack.reserve(16);

    PyObject* result = nullptr;   // The finished root object.
    PyObject* pending = nullptr;  // A value awaiting insertion into stack.back().
    // The key `pending` goes under, when stack.back() is an object. Valid only
    // while `pending` is non-null.
    const char* pending_key = nullptr;
    std::size_t pending_key_len = 0;

    /// Push a new container frame. `key`/`key_len` describe where the container
    /// belongs in its parent and are stored on the frame, not in pending_key,
    /// because iterating the new container overwrites pending_key repeatedly.
    const auto open_container = [&](yyjson_val* val, const char* key, std::size_t key_len) noexcept -> bool {
        if (stack.size() >= kMaxDepth) {
            PyErr_SetString(PyExc_ValueError, "Maximum JSON nesting depth exceeded");
            return false;
        }
        const bool is_object = yyjson_is_obj(val);
        PyObject* container = is_object ? PyDict_New() : PyList_New(0);
        if (!container) return false;
        Frame frame{};
        frame.container = container;
        frame.val = val;
        frame.is_object = is_object;
        frame.parent_key = key;
        frame.parent_key_len = key_len;
        if (is_object) {
            yyjson_obj_iter_init(val, &frame.obj_iter);
        } else {
            yyjson_arr_iter_init(val, &frame.arr_iter);
        }
        stack.push_back(frame);
        return true;
    };

    const auto unwind = [&stack]() noexcept {
        for (Frame& f : stack) Py_XDECREF(f.container);
        stack.clear();
    };

    if (yyjson_is_obj(root) || yyjson_is_arr(root)) {
        if (!open_container(root, nullptr, 0)) {
            yyjson_doc_free(doc);
            return nullptr;
        }
    } else {
        result = scalar_to_python(root);
        yyjson_doc_free(doc);
        return result;
    }

    while (!stack.empty()) {
        Frame& frame = stack.back();

        // Insert any value produced by the previous iteration.
        if (pending) {
            bool ok;
            if (frame.is_object) {
                PyObject* key =
                    PyUnicode_DecodeUTF8(pending_key, static_cast<Py_ssize_t>(pending_key_len), "strict");
                if (!key) {
                    Py_DECREF(pending);
                    unwind();
                    yyjson_doc_free(doc);
                    return nullptr;
                }
                // Last-wins on duplicates, matching json.loads.
                ok = PyDict_SetItem(frame.container, key, pending) == 0;
                Py_DECREF(key);
            } else {
                ok = PyList_Append(frame.container, pending) == 0;
            }
            Py_DECREF(pending);
            pending = nullptr;
            if (!ok) {
                unwind();
                yyjson_doc_free(doc);
                return nullptr;
            }
        }

        // Pull the next child.
        yyjson_val* child = nullptr;
        const char* child_key = nullptr;
        std::size_t child_key_len = 0;
        if (frame.is_object) {
            yyjson_val* key = yyjson_obj_iter_next(&frame.obj_iter);
            if (key) {
                child_key = yyjson_get_str(key);
                child_key_len = yyjson_get_len(key);
                child = yyjson_obj_iter_get_val(key);
            }
        } else {
            child = yyjson_arr_iter_next(&frame.arr_iter);
        }

        if (!child) {
            // Container exhausted: it becomes the pending value of its parent,
            // stored under the key recorded when this frame was pushed.
            PyObject* finished = frame.container;
            const char* own_key = frame.parent_key;
            const std::size_t own_key_len = frame.parent_key_len;
            stack.pop_back();
            if (stack.empty()) {
                result = finished;  // Transfers the reference to the caller.
                break;
            }
            pending = finished;
            pending_key = own_key;
            pending_key_len = own_key_len;
            continue;
        }

        if (yyjson_is_obj(child) || yyjson_is_arr(child)) {
            if (!open_container(child, child_key, child_key_len)) {
                unwind();
                yyjson_doc_free(doc);
                return nullptr;
            }
            continue;
        }

        pending = scalar_to_python(child);
        if (!pending) {
            unwind();
            yyjson_doc_free(doc);
            return nullptr;
        }
        pending_key = child_key;
        pending_key_len = child_key_len;
    }

    yyjson_doc_free(doc);
    return result;
}

}  // namespace json
}  // namespace aq
