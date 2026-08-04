// numeric.hpp -- integer and float formatting for the JSON encoder.
//
// Both exist because the obvious implementations are slow in ways that show up
// on a response path:
//
//   * Integers via PyObject_Str() allocate a Python str, encode it to UTF-8, copy
//     the bytes out, and free it. For a value that fits in a machine word that is
//     four unnecessary steps; write_int64 does none of them.
//
//   * Floats via repr() have the same problem plus a subtler one: the result must
//     round-trip. CPython's repr() produces the shortest string that reparses
//     exactly, and a naive "%.17g" does not -- it is both longer and, for some
//     values, not shortest-round-trip. write_double therefore uses
//     PyOS_double_to_string with 'r' (repr mode), which is the same shortest
//     round-trip algorithm CPython itself uses, without materialising a str.
//
// JSON has no representation for NaN or +/-Infinity. Both are rejected rather
// than emitted as bare tokens: `NaN` is invalid JSON that many parsers accept,
// so writing it produces output that silently fails elsewhere.
#pragma once

#include <Python.h>

#include <cmath>
#include <cstddef>
#include <cstdint>

#include "buffer.hpp"
#include "yyjson_dtoa.h"

namespace aq {
namespace json {

/// Longest decimal int64: "-9223372036854775808" is 20 chars.
inline constexpr std::size_t kMaxInt64Digits = 20;

/// Write a signed 64-bit integer in decimal.
///
/// Digits are generated least-significant first into a scratch array and then
/// reversed, which avoids a division to find the digit count up front.
///
/// @param v   Value to write.
/// @param out Destination.
/// @returns   false only on allocation failure.
[[nodiscard]] inline bool write_int64(std::int64_t v, Buffer& out) noexcept {
    char* dst = out.reserve_raw(kMaxInt64Digits + 1);
    if (!dst) return false;

    std::size_t n = 0;
    if (v < 0) {
        dst[n++] = '-';
        // Negate through uint64 so INT64_MIN does not overflow.
        std::uint64_t mag = static_cast<std::uint64_t>(-(v + 1)) + 1;
        char tmp[kMaxInt64Digits];
        std::size_t t = 0;
        do {
            tmp[t++] = static_cast<char>('0' + (mag % 10));
            mag /= 10;
        } while (mag);
        while (t) dst[n++] = tmp[--t];
    } else {
        std::uint64_t mag = static_cast<std::uint64_t>(v);
        char tmp[kMaxInt64Digits];
        std::size_t t = 0;
        do {
            tmp[t++] = static_cast<char>('0' + (mag % 10));
            mag /= 10;
        } while (mag);
        while (t) dst[n++] = tmp[--t];
    }
    out.commit(n);
    return true;
}

/// Write an unsigned 64-bit integer in decimal.
///
/// Separate from write_int64 because Python ints above INT64_MAX but within
/// UINT64_MAX are common enough (hashes, ids, flags) to be worth keeping on the
/// fast path rather than falling back to PyObject_Str.
[[nodiscard]] inline bool write_uint64(std::uint64_t v, Buffer& out) noexcept {
    char* dst = out.reserve_raw(kMaxInt64Digits + 1);
    if (!dst) return false;
    char tmp[kMaxInt64Digits + 1];
    std::size_t t = 0;
    do {
        tmp[t++] = static_cast<char>('0' + (v % 10));
        v /= 10;
    } while (v);
    std::size_t n = 0;
    while (t) dst[n++] = tmp[--t];
    out.commit(n);
    return true;
}

/// Write a double using shortest-round-trip formatting.
///
/// Two paths. The fast one handles doubles that are exactly a small integer --
/// scores, counts, quantised measurements -- with the integer writer and a ".0"
/// suffix, skipping decimal conversion entirely.
///
/// The general path uses yyjson's formatter via :c:func:`aq_yyjson_write_double`,
/// which writes into a stack buffer and allocates nothing. The obvious
/// alternative, ``PyOS_double_to_string``, is correct but mallocs and frees per
/// value; on 5000 fractional floats that cost 380us against 118us here.
///
/// Both paths produce the shortest string that reparses to exactly the input,
/// which is what ``repr()`` guarantees and what round-tripping requires. A
/// naive ``"%.17g"`` is both longer and, for some values, not shortest.
///
/// @param v   Value to write.
/// @param out Destination.
/// @returns   false on allocation failure, or when `v` is NaN or infinite -- in
///            which case a Python ValueError is set, because there is no valid
///            JSON for those and emitting a bare `NaN` token produces output
///            that only some parsers accept.
[[nodiscard]] inline bool write_double(double v, Buffer& out) noexcept {
    // JSON cannot represent these, and yyjson's writer does not check.
    if (!std::isfinite(v)) {
        PyErr_SetString(PyExc_ValueError, "Out of range float values are not JSON compliant");
        return false;
    }

    // Fast path: an exact integral value inside the range where a double
    // represents every integer exactly (2^53). Both bounds matter -- above 2^53
    // the cast is lossy, and the `== v` test is what rejects fractions.
    if (v >= -9007199254740992.0 && v <= 9007199254740992.0) {
        const std::int64_t as_int = static_cast<std::int64_t>(v);
        if (static_cast<double>(as_int) == v) {
            // Negative zero must not take this path: (int64)-0.0 is 0, so it
            // would print "0.0" and drop the sign that repr() preserves.
            if (as_int != 0 || !std::signbit(v)) {
                if (!write_int64(as_int, out)) return false;
                return out.append(".0", 2);
            }
        }
    }

    char scratch[AQ_DTOA_BUF_SIZE];
    char* end = aq_yyjson_write_double(v, scratch);
    return out.append(scratch, static_cast<std::size_t>(end - scratch));
}

}  // namespace json
}  // namespace aq
