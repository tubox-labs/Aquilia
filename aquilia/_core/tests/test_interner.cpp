// C++ unit tests for aq::Interner. Phase 9C.
#include "harness.hpp"
#include "interner.hpp"

#include <string>

using namespace aq;

TEST(Interner, IdempotentIntern) {
    Interner in;
    const auto a = in.intern("users");
    const auto b = in.intern("users");
    EXPECT_EQ(a, b);
    EXPECT_EQ(in.get(a), std::string_view("users"));
    EXPECT_EQ(in.size(), 1u);
}

TEST(Interner, DifferentStrings) {
    Interner in;
    EXPECT_NE(in.intern("a"), in.intern("b"));
    EXPECT_EQ(in.size(), 2u);
}

TEST(Interner, EmptyString) {
    Interner in;
    const auto id = in.intern("");
    EXPECT_EQ(in.get(id).size(), 0u);
    EXPECT_EQ(in.intern(""), id);
}

TEST(Interner, LookupDoesNotInsert) {
    Interner in;
    EXPECT_EQ(in.lookup("absent"), NO_INTERN);
    EXPECT_EQ(in.size(), 0u);
    const auto id = in.intern("present");
    EXPECT_EQ(in.lookup("present"), id);
}

TEST(Interner, InvalidIdReturnsEmpty) {
    Interner in;
    EXPECT_EQ(in.get(0).size(), 0u);
    EXPECT_EQ(in.get(NO_INTERN).size(), 0u);
}

TEST(Interner, NullBytes) {
    // Keys are opaque bytes: embedded NULs must not truncate.
    Interner in;
    const std::string a("x\0y", 3);
    const std::string b("x\0z", 3);
    const auto ia = in.intern(a);
    const auto ib = in.intern(b);
    EXPECT_NE(ia, ib);
    EXPECT_EQ(in.get(ia).size(), 3u);
    EXPECT_EQ(in.intern(a), ia);
}

TEST(Interner, InvalidUtf8) {
    Interner in;
    const std::string bad("\xff\xfe\xfd", 3);
    const auto id = in.intern(bad);
    EXPECT_EQ(in.get(id).size(), 3u);
    EXPECT_EQ(in.lookup(bad), id);
}

TEST(Interner, LargeVolumeKeepsViewsValid) {
    // Regression guard: keys are views into owned storage. If that storage were
    // held by value in a vector, growth would invalidate every existing key and
    // lookups would read freed memory. ASAN catches this if it regresses.
    Interner in;
    for (int i = 0; i < 10000; ++i) {
        in.intern("segment-" + std::to_string(i));
    }
    EXPECT_EQ(in.size(), 10000u);
    for (int i = 0; i < 10000; i += 997) {
        const std::string s = "segment-" + std::to_string(i);
        EXPECT_EQ(in.get(in.lookup(s)), std::string_view(s));
    }
}

TEST(Interner, IdsAreDenseAndOrdered) {
    Interner in;
    EXPECT_EQ(in.intern("first"), 0u);
    EXPECT_EQ(in.intern("second"), 1u);
    EXPECT_EQ(in.intern("first"), 0u);
    EXPECT_EQ(in.intern("third"), 2u);
}

int main() { return aqtest::run_all(); }
