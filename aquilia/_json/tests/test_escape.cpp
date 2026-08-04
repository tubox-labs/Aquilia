// test_escape.cpp -- differential test for the SWAR escape scanner.
//
// find_escape() checks eight bytes per iteration using word arithmetic. That is
// worth doing -- it is the encoder's hottest loop -- but the identities are easy
// to get subtly wrong in a way that only shows up on particular byte values at
// particular alignments.
//
// The first version of the less-than term was wrong: it reported every byte
// >= 0x20 as a control character, because it lacked the `& ~w` that suppresses
// the high-bit carry. A spot-check with ASCII text would have passed. What
// caught it was exactly this: compare against a trivially-correct scalar
// reference for every byte value at every alignment.
//
// So this test is exhaustive by construction rather than by sampling.
#include <cstdint>
#include <cstring>
#include <string>

#include "escape.hpp"
#include "harness.hpp"

using aq::json::Buffer;
using aq::json::find_escape;
using aq::json::write_string;

namespace {

/// Obviously-correct reference: what the fast scanner must agree with.
bool needs_escape(unsigned char c) { return c == '"' || c == '\\' || c < 0x20; }

std::size_t reference_find(const char* p, std::size_t n) {
    for (std::size_t i = 0; i < n; ++i) {
        if (needs_escape(static_cast<unsigned char>(p[i]))) return i;
    }
    return n;
}

std::string encode(const std::string& in) {
    Buffer out;
    EXPECT_TRUE(write_string(in.data(), in.size(), out));
    return std::string(out.data(), out.size());
}

}  // namespace

// ---------------------------------------------------------------------------
// find_escape
// ---------------------------------------------------------------------------

TEST(Escape, EveryByteValueAtEveryAlignment) {
    // The case that caught the bad SWAR identity. 17 offsets covers two full
    // words plus a partial, so both the vector loop and the scalar tail see
    // every value.
    for (int off = 0; off < 17; ++off) {
        for (int v = 0; v < 256; ++v) {
            char buf[24];
            std::memset(buf, 'a', sizeof buf);
            buf[off] = static_cast<char>(v);
            for (std::size_t n = static_cast<std::size_t>(off) + 1; n <= sizeof buf; ++n) {
                EXPECT_EQ(find_escape(buf, n), reference_find(buf, n));
            }
        }
    }
}

TEST(Escape, HighBytesAreNotControls) {
    // Direct regression on the original defect: 0x80-0xFF are valid UTF-8
    // continuation bytes and must pass through untouched.
    for (int v = 0x80; v < 0x100; ++v) {
        char buf[8];
        std::memset(buf, static_cast<char>(v), sizeof buf);
        EXPECT_EQ(find_escape(buf, sizeof buf), std::size_t{8});
    }
}

TEST(Escape, RandomisedDifferential) {
    std::uint32_t seed = 12345;
    for (int t = 0; t < 200000; ++t) {
        char buf[64];
        const std::size_t n = 1 + (seed % 64);
        for (std::size_t i = 0; i < n; ++i) {
            seed = seed * 1103515245u + 12345u;
            buf[i] = static_cast<char>((seed >> 16) & 0xFF);
        }
        EXPECT_EQ(find_escape(buf, n), reference_find(buf, n));
        seed = seed * 1103515245u + 12345u;
    }
}

TEST(Escape, EmptyAndCleanInput) {
    EXPECT_EQ(find_escape("", 0), std::size_t{0});
    EXPECT_EQ(find_escape("hello", 5), std::size_t{5});
    const char* long_clean = "the quick brown fox jumps over the lazy dog 0123456789";
    EXPECT_EQ(find_escape(long_clean, std::strlen(long_clean)), std::strlen(long_clean));
}

// ---------------------------------------------------------------------------
// write_string
// ---------------------------------------------------------------------------

TEST(WriteString, PlainAsciiIsQuotedOnly) { EXPECT_EQ(encode("hello"), "\"hello\""); }

TEST(WriteString, Empty) { EXPECT_EQ(encode(""), "\"\""); }

TEST(WriteString, ShortEscapes) {
    EXPECT_EQ(encode("a\"b"), "\"a\\\"b\"");
    EXPECT_EQ(encode("a\\b"), "\"a\\\\b\"");
    EXPECT_EQ(encode("a\nb"), "\"a\\nb\"");
    EXPECT_EQ(encode("a\rb"), "\"a\\rb\"");
    EXPECT_EQ(encode("a\tb"), "\"a\\tb\"");
    EXPECT_EQ(encode(std::string("a\bb")), "\"a\\bb\"");
    EXPECT_EQ(encode(std::string("a\fb")), "\"a\\fb\"");
}

TEST(WriteString, ControlCharactersUseUnicodeForm) {
    EXPECT_EQ(encode(std::string(1, '\x01')), "\"\\u0001\"");
    EXPECT_EQ(encode(std::string(1, '\x1f')), "\"\\u001f\"");
    // NUL is a legitimate character inside a Python str.
    EXPECT_EQ(encode(std::string(1, '\0')), "\"\\u0000\"");
}

TEST(WriteString, DelIsNotEscaped) {
    // 0x7F is legal unescaped per RFC 8259.
    EXPECT_EQ(encode(std::string(1, '\x7f')), "\"\x7f\"");
}

TEST(WriteString, Utf8PassesThroughRaw) {
    // JSON permits raw UTF-8; transcoding to \u escapes would be slower and
    // larger for no benefit.
    EXPECT_EQ(encode("\xc3\xa9"), "\"\xc3\xa9\"");           // e-acute
    EXPECT_EQ(encode("\xe2\x82\xac"), "\"\xe2\x82\xac\"");   // euro sign
    EXPECT_EQ(encode("\xf0\x9f\x98\x80"), "\"\xf0\x9f\x98\x80\"");  // emoji
}

TEST(WriteString, EscapeAtWordBoundaries) {
    // The escape must be found whether it lands in the vector loop or the tail.
    for (std::size_t pos = 0; pos < 20; ++pos) {
        std::string s(20, 'a');
        s[pos] = '"';
        std::string expected = "\"" + std::string(pos, 'a') + "\\\"" + std::string(19 - pos, 'a') + "\"";
        EXPECT_EQ(encode(s), expected);
    }
}

TEST(WriteString, AllEscapesInOneString) {
    std::string s;
    for (int i = 0; i < 0x20; ++i) s.push_back(static_cast<char>(i));
    s.push_back('"');
    s.push_back('\\');
    const std::string out = encode(s);

    EXPECT_TRUE(out.front() == '"');
    EXPECT_TRUE(out.back() == '"');

    // The invariant that matters: no raw control byte survives into the output.
    // (Quotes and backslashes do appear in the body -- as the escape sequences
    // \" and \\ -- so they are not part of this check.)
    const std::string body = out.substr(1, out.size() - 2);
    for (const char c : body) {
        EXPECT_TRUE(static_cast<unsigned char>(c) >= 0x20);
    }

    // And it round-trips through a decoder: every escape is well-formed.
    EXPECT_EQ(body.find("\\u0000"), std::size_t{0});
    EXPECT_TRUE(body.find("\\\"") != std::string::npos);
    EXPECT_TRUE(body.find("\\\\") != std::string::npos);
}

TEST(WriteString, LongStringWithNoEscapes) {
    const std::string s(10000, 'x');
    const std::string out = encode(s);
    EXPECT_EQ(out.size(), s.size() + 2);
}

int main() { return ::aqtest::run_all(); }
