// uuid_parse.hpp -- canonical UUID string -> normalised 32-char hex.
//
// Deliberately Python-free so it can be unit tested and sanitized without an
// interpreter in the process (see tests/CMakeLists.txt).
//
// Why this is the one conversion worth writing natively: docs/models-engine/02
// section 3 measures uuid.UUID(str) at ~354 ns against a ~43-55 ns boundary
// crossing, and it is slow precisely because uuid.UUID.__init__ is *pure
// Python* -- three str.replace calls plus strip/count/len per parse
// (CPython Lib/uuid.py). Every other scalar conversion in the ORM is already C
// and costs less than one crossing, which is what refuted a per-field native
// API. UUID and JSON are the only per-value wins.
#pragma once

#include <cstddef>
#include <string_view>

namespace aq {

// Number of bytes normalise_uuid_hex writes, including the trailing NUL.
inline constexpr std::size_t kUuidHexBufSize = 33;

// Validate a UUID string and write its 32 hex digits, NUL-terminated, to `out`.
//
// Returns false for anything this parser does not handle with *certainty*. The
// caller must then fall back to Python's uuid.UUID, which holds the
// authoritative semantics. A false reject only costs speed on unusual input; a
// false accept would be a silent correctness bug, so the accepted grammar is
// kept deliberately narrow.
//
// On success `out` contains only [0-9a-fA-F], which is what makes it safe to
// hand to PyLong_FromString(base=16): that function would otherwise also accept
// underscores, signs, and surrounding whitespace.
//
// Accepted:
//   550e8400-e29b-41d4-a716-446655440000    canonical, hyphens at 8-4-4-4-12
//   550e8400e29b41d4a716446655440000        no hyphens
//   {...}                                   either of the above in braces
//   urn:uuid:...                            either of the above, urn-prefixed
//   upper, lower, and mixed case hex
//
// Rejected (deferred to Python, which accepts several of them):
//   underscores       int(hex, 16) allows digit separators: "1234_678..." is a
//                     valid UUID to CPython
//   leading + or -    int() accepts a sign
//   whitespace        int() strips it
//   non-ASCII digits  int() accepts any Unicode Nd character
//   hyphens in non-canonical positions, which CPython strips from anywhere
bool normalise_uuid_hex(std::string_view s, char out[kUuidHexBufSize]) noexcept;

}  // namespace aq
