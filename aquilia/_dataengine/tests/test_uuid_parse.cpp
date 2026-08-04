// C++ unit tests for the UUID hex normaliser.
//
// The accepted grammar is deliberately narrower than CPython's, so these tests
// come in two halves: the forms that must normalise identically, and the forms
// that must be *rejected* so the caller falls back to Python rather than parsing
// them differently. The second half is the one that matters -- a false accept
// is a silent correctness bug, a false reject only costs speed.

#include "harness.hpp"
#include "uuid_parse.hpp"

#include <cstddef>
#include <string>
#include <string_view>

using aq::kUuidHexBufSize;
using aq::normalise_uuid_hex;

namespace {

bool normalises_to(const char* s, const char* want) {
    char out[kUuidHexBufSize] = {};
    if (!normalise_uuid_hex(s, out)) return false;
    return std::string(out) == want;
}

bool parses_to_expected(const char* s) {
    return normalises_to(s, "550e8400e29b41d4a716446655440000");
}

bool rejects(const char* s) {
    char out[kUuidHexBufSize] = {};
    return !normalise_uuid_hex(s, out);
}

}  // namespace

TEST(uuid, canonical_lowercase) {
    EXPECT_TRUE(parses_to_expected("550e8400-e29b-41d4-a716-446655440000"));
}

TEST(uuid, canonical_uppercase) {
    // Case is preserved rather than folded: PyLong_FromString(base=16) accepts
    // either, so folding would be wasted work on every parse.
    EXPECT_TRUE(normalises_to("550E8400-E29B-41D4-A716-446655440000",
                              "550E8400E29B41D4A716446655440000"));
}

TEST(uuid, canonical_mixed_case) {
    EXPECT_TRUE(normalises_to("550e8400-E29B-41d4-A716-446655440000",
                              "550e8400E29B41d4A716446655440000"));
}

TEST(uuid, no_hyphens) {
    EXPECT_TRUE(parses_to_expected("550e8400e29b41d4a716446655440000"));
}

TEST(uuid, braces) {
    EXPECT_TRUE(parses_to_expected("{550e8400-e29b-41d4-a716-446655440000}"));
}

TEST(uuid, braces_without_hyphens) {
    EXPECT_TRUE(parses_to_expected("{550e8400e29b41d4a716446655440000}"));
}

TEST(uuid, urn_prefix) {
    EXPECT_TRUE(parses_to_expected("urn:uuid:550e8400-e29b-41d4-a716-446655440000"));
}

TEST(uuid, urn_prefix_and_braces) {
    EXPECT_TRUE(parses_to_expected("urn:uuid:{550e8400-e29b-41d4-a716-446655440000}"));
}

TEST(uuid, all_zeroes) {
    EXPECT_TRUE(normalises_to("00000000-0000-0000-0000-000000000000",
                              "00000000000000000000000000000000"));
}

TEST(uuid, all_ones) {
    EXPECT_TRUE(normalises_to("ffffffff-ffff-ffff-ffff-ffffffffffff",
                              "ffffffffffffffffffffffffffffffff"));
}

TEST(uuid, every_hex_digit_survives) {
    EXPECT_TRUE(normalises_to("01234567-89ab-cdef-0123-456789abcdef",
                              "0123456789abcdef0123456789abcdef"));
}

TEST(uuid, output_is_nul_terminated) {
    // PyLong_FromString reads to the NUL, so the terminator is load-bearing:
    // without it the parse would run into whatever follows in the buffer.
    char out[kUuidHexBufSize];
    for (std::size_t i = 0; i < kUuidHexBufSize; ++i) out[i] = 'X';
    EXPECT_TRUE(normalise_uuid_hex("550e8400-e29b-41d4-a716-446655440000", out));
    EXPECT_EQ(out[32], '\0');
    EXPECT_EQ(std::string(out).size(), static_cast<std::size_t>(32));
}

// -- Rejections. Each of these is something CPython ACCEPTS; normalising them
// here would diverge, so they must fall back instead.

TEST(uuid_reject, underscore_separator) {
    // int(hex, 16) allows digit separators, so CPython reads this as a valid
    // UUID. 32 characters, so a length check alone would not catch it.
    EXPECT_TRUE(rejects("1234_678123456781234567812345678"));
}

TEST(uuid_reject, leading_plus) {
    EXPECT_TRUE(rejects("+1234567812345678123456781234567"));
}

TEST(uuid_reject, leading_minus) {
    EXPECT_TRUE(rejects("-1234567812345678123456781234567"));
}

TEST(uuid_reject, leading_whitespace) {
    EXPECT_TRUE(rejects(" 50e8400e29b41d4a716446655440000"));
}

TEST(uuid_reject, trailing_whitespace) {
    EXPECT_TRUE(rejects("550e8400e29b41d4a71644665544000 "));
}

TEST(uuid_reject, hyphens_in_wrong_places) {
    // CPython strips hyphens from anywhere; this parser only accepts them at
    // the canonical 8-4-4-4-12 offsets.
    EXPECT_TRUE(rejects("5-50e8400-e29b-41d4-a716-44665544000"));
}

// -- Rejections that CPython also rejects.

TEST(uuid_reject, non_hex_character) {
    EXPECT_TRUE(rejects("550e8400-e29b-41d4-a716-44665544000g"));
}

TEST(uuid_reject, too_short) {
    EXPECT_TRUE(rejects("550e8400-e29b-41d4-a716-4466554400"));
}

TEST(uuid_reject, too_long) {
    EXPECT_TRUE(rejects("550e8400-e29b-41d4-a716-4466554400000"));
}

TEST(uuid_reject, empty) {
    EXPECT_TRUE(rejects(""));
}

TEST(uuid_reject, wrong_separator) {
    EXPECT_TRUE(rejects("550e8400:e29b:41d4:a716:446655440000"));
}

TEST(uuid_reject, high_byte_utf8) {
    // A UTF-8 continuation byte must not be read as a hex digit. The table maps
    // every byte >= 0x80 to invalid, so this falls out of the same check.
    EXPECT_TRUE(rejects("550e8400-e29b-41d4-a716-4466554400\xc3\xa9"));
}

TEST(uuid_reject, unbalanced_brace) {
    EXPECT_TRUE(rejects("{550e8400-e29b-41d4-a716-446655440000"));
}

TEST(uuid_reject, embedded_null) {
    // string_view carries an explicit length, so an interior NUL must be
    // treated as a non-hex byte rather than terminating the scan.
    // Built by mutation rather than from a literal with an octal escape:
    // "\0000" is \000 followed by '0', which is 34 bytes, not 36 -- an earlier
    // version of this test read past the literal, and ASAN caught it.
    std::string s = "550e8400-e29b-41d4-a716-446655440000";
    EXPECT_EQ(s.size(), static_cast<std::size_t>(36));
    s[20] = '\0';
    char out[kUuidHexBufSize] = {};
    EXPECT_TRUE(!normalise_uuid_hex(std::string_view(s.data(), s.size()), out));
}

int main() { return ::aqtest::run_all(); }
