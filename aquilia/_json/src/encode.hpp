// encode.hpp -- Python object graph -> UTF-8 JSON bytes.
#pragma once

#include <Python.h>

#include <cstddef>

#include "buffer.hpp"

namespace aq {
namespace json {

/// Maximum container nesting the encoder will follow.
///
/// A limit is required, not optional: without one, a self-referential structure
/// is an infinite loop and a deeply nested one is a memory exhaustion. 1024 is
/// far above any legitimate payload and far below anything that strains the
/// work stack.
inline constexpr std::size_t kMaxDepth = 1024;

/// Outcome of an encode. Errors are returned rather than thrown -- an exception
/// on the response path costs more than the encode it reports on.
enum class EncodeStatus {
    Ok = 0,
    /// A Python exception is set. The caller must propagate it.
    Error = 1,
};

/// Serialise `obj` into `out` as UTF-8 JSON.
///
/// Container traversal uses an explicit work stack rather than recursion, so a
/// deeply nested payload cannot overflow the C stack -- it hits kMaxDepth and
/// returns a clean error instead of crashing the process. That distinction is
/// the difference between a 400 and a segfault, and adversarial JSON is exactly
/// where a recursive encoder fails.
///
/// Type dispatch compares `Py_TYPE(obj)` against the exact type objects rather
/// than using PyDict_Check and friends: the Check macros walk the MRO for
/// subclasses, and the common case is an exact builtin. Subclasses still work --
/// they fall through to the slower isinstance-based path.
///
/// @param obj      Borrowed reference to the root object.
/// @param default_fn  Called for objects the encoder cannot represent directly.
///                    May be null, in which case such objects are an error.
/// @param out      Destination buffer; appended to, never truncated.
/// @returns        Ok, or Error with a Python exception set.
[[nodiscard]] EncodeStatus encode(PyObject* obj, PyObject* default_fn, Buffer& out) noexcept;

}  // namespace json
}  // namespace aq
