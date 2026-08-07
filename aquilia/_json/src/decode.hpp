// decode.hpp -- UTF-8 JSON bytes -> Python objects.
#pragma once

#include <Python.h>

#include <cstddef>

namespace aq {
namespace json {

/// Parse `data` into a new Python object.
///
/// Unlike encoding, decoding is where yyjson wins outright: it owns the parse,
/// allocates the whole document from one arena rather than per node, and reads
/// at rates CPython's parser cannot approach. The Python objects are then built
/// in a single walk of the resulting immutable tree.
///
/// Nesting is bounded by kMaxDepth via an explicit work stack, for the same
/// reason as the encoder: recursion on attacker-controlled input is a crash, not
/// an error.
///
/// @param data  UTF-8 bytes. Not required to be NUL-terminated.
/// @param len   Byte length.
/// @returns     A new reference, or nullptr with a Python exception set.
[[nodiscard]] PyObject* decode(const char* data, std::size_t len) noexcept;

}  // namespace json
}  // namespace aq
