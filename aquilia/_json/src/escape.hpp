// escape.hpp -- JSON string escaping.
//
// This is the encoder's hottest inner loop: every key and every string value
// passes through it. The design follows from one observation -- the overwhelming
// majority of JSON strings contain no character that needs escaping at all. So
// the fast path is "scan for the first byte that needs work, bulk-copy
// everything before it", not "test and append one byte at a time".
//
// Two levels:
//
//   * A 256-entry table classifies bytes. Table lookup beats a chain of
//     comparisons and, unlike a comparison chain, costs the same for every byte.
//
//   * Word-at-a-time scanning checks eight bytes per iteration using the
//     standard SWAR trick, so a clean 200-byte string is scanned in ~25
//     iterations rather than 200. This is portable arithmetic, not intrinsics:
//     it needs no runtime dispatch, no -march flags, and compiles to the same
//     thing on x86-64 and AArch64.
//
// What must be escaped, per RFC 8259: the quote, the backslash, and everything
// below 0x20. DEL (0x7F) is legal unescaped and is left alone. Bytes >= 0x80 are
// passed through untouched, which is what makes the non-ASCII path free -- the
// input is already valid UTF-8 (CPython guarantees it for str) and JSON permits
// raw UTF-8.
#pragma once

#include <cstddef>
#include <cstdint>
#include <cstring>

#include "buffer.hpp"

namespace aq {
namespace json {

/// Per-byte escape classification.
enum : std::uint8_t {
    kEscNone = 0,  ///< Emit as-is.
    kEscShort = 1, ///< Has a two-character form: \" \\ \n \r \t \b \f
    kEscUnicode = 2 ///< Needs \u00XX (the remaining C0 controls).
};

/// Classification table for all 256 byte values.
///
/// Built once as a constexpr array so it lands in .rodata rather than being
/// computed at startup.
struct EscapeTable {
    std::uint8_t kind[256]{};
    char shortcut[256]{};

    constexpr EscapeTable() {
        for (int i = 0; i < 0x20; ++i) {
            kind[i] = kEscUnicode;
        }
        kind[static_cast<unsigned char>('"')] = kEscShort;
        shortcut[static_cast<unsigned char>('"')] = '"';
        kind[static_cast<unsigned char>('\\')] = kEscShort;
        shortcut[static_cast<unsigned char>('\\')] = '\\';
        kind[static_cast<unsigned char>('\n')] = kEscShort;
        shortcut[static_cast<unsigned char>('\n')] = 'n';
        kind[static_cast<unsigned char>('\r')] = kEscShort;
        shortcut[static_cast<unsigned char>('\r')] = 'r';
        kind[static_cast<unsigned char>('\t')] = kEscShort;
        shortcut[static_cast<unsigned char>('\t')] = 't';
        kind[0x08] = kEscShort;
        shortcut[0x08] = 'b';
        kind[0x0C] = kEscShort;
        shortcut[0x0C] = 'f';
    }
};

inline constexpr EscapeTable kEscapeTable{};

inline constexpr char kHexDigits[] = "0123456789abcdef";

/// Find the offset of the first byte in [p, p+n) that needs escaping.
///
/// Scans eight bytes per iteration. For each 8-byte word we need "does any byte
/// equal '"', equal '\\', or fall below 0x20". Two SWAR identities do it:
///
///   * **Equality.** `(x - 0x0101..01) & ~x & 0x8080..80` sets the high bit of
///     every zero byte of `x`. XOR-ing the word with a broadcast byte first
///     turns "is any byte equal to c" into "is any byte zero".
///
///   * **Less-than.** `(w - 0x2020..20) & ~w & 0x8080..80` sets the high bit of
///     every byte below 0x20. The `& ~w` term is what makes it correct for
///     arbitrary input: without it, a byte >= 0x80 keeps its own high bit after
///     the subtract and is reported as a control character. That is not a
///     theoretical concern -- it fires on the first non-ASCII string, and the
///     differential test in tests/test_escape.cpp covers every byte value at
///     every alignment because of it.
///
/// @returns The index of the first byte needing an escape, or `n` when none does.
[[nodiscard]] inline std::size_t find_escape(const char* p, std::size_t n) noexcept {
    constexpr std::uint64_t kOnes = 0x0101010101010101ULL;
    constexpr std::uint64_t kHighs = 0x8080808080808080ULL;
    constexpr std::uint64_t kQuote = 0x2222222222222222ULL;   // '"' broadcast
    constexpr std::uint64_t kBacksl = 0x5C5C5C5C5C5C5C5CULL;  // '\\' broadcast
    constexpr std::uint64_t kSpaces = 0x2020202020202020ULL;  // 0x20 broadcast

    std::size_t i = 0;
    for (; i + 8 <= n; i += 8) {
        std::uint64_t w;
        std::memcpy(&w, p + i, 8);

        const std::uint64_t q = w ^ kQuote;
        const std::uint64_t b = w ^ kBacksl;
        const std::uint64_t has_quote = (q - kOnes) & ~q & kHighs;
        const std::uint64_t has_backslash = (b - kOnes) & ~b & kHighs;
        const std::uint64_t has_control = (w - kSpaces) & ~w & kHighs;

        if (has_quote | has_backslash | has_control) {
            // A flagged word: find which byte, one at a time. Rare enough that
            // the scalar loop costs nothing overall.
            for (std::size_t j = i; j < i + 8; ++j) {
                if (kEscapeTable.kind[static_cast<unsigned char>(p[j])] != kEscNone) return j;
            }
        }
    }
    for (; i < n; ++i) {
        if (kEscapeTable.kind[static_cast<unsigned char>(p[i])] != kEscNone) return i;
    }
    return n;
}

/// Write a UTF-8 byte range as a quoted, escaped JSON string.
///
/// @param p   Source bytes; must be valid UTF-8 (CPython guarantees this for
///            `str`, and JSON permits raw UTF-8, so no transcoding happens).
/// @param n   Byte length.
/// @param out Destination.
/// @returns   false only on allocation failure.
[[nodiscard]] inline bool write_string(const char* p, std::size_t n, Buffer& out) noexcept {
    // Worst case is every byte becoming \u00XX, but reserving 6n up front would
    // balloon the buffer for input that almost never needs it. Reserve for the
    // clean case plus quotes and let the escape path grow on demand.
    if (!out.reserve_extra(n + 2)) return false;
    out.put_unchecked('"');

    std::size_t pos = 0;
    while (pos < n) {
        const std::size_t stop = find_escape(p + pos, n - pos);
        if (stop > 0) {
            // Bulk-copy the clean run. This is where the win is: one memcpy for
            // an entire unescaped string.
            if (!out.append(p + pos, stop)) return false;
            pos += stop;
            if (pos >= n) break;
        }

        const unsigned char c = static_cast<unsigned char>(p[pos]);
        const std::uint8_t kind = kEscapeTable.kind[c];
        if (kind == kEscShort) {
            if (!out.reserve_extra(2)) return false;
            out.put_unchecked('\\');
            out.put_unchecked(kEscapeTable.shortcut[c]);
        } else {
            // Remaining C0 control: \u00XX.
            if (!out.reserve_extra(6)) return false;
            out.put_unchecked('\\');
            out.put_unchecked('u');
            out.put_unchecked('0');
            out.put_unchecked('0');
            out.put_unchecked(kHexDigits[(c >> 4) & 0xF]);
            out.put_unchecked(kHexDigits[c & 0xF]);
        }
        ++pos;
    }

    return out.put('"');
}

}  // namespace json
}  // namespace aq
