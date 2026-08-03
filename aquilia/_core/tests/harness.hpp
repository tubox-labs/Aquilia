// harness.hpp -- 40-line assertion harness for the engine's C++ unit tests.
//
// Not GoogleTest: FetchContent needs network at configure time and adds ~30s to
// a cold build, and nothing here needs fixtures, mocks, parameterisation, or
// death tests. TEST/EXPECT_* keep the same shape as the specs in
// docs/engine/07-testing-strategy.md so the tests read the same either way.
#pragma once

#include <cstdio>
#include <string>
#include <string_view>
#include <type_traits>
#include <vector>

namespace aqtest {

struct Case {
    const char* suite;
    const char* name;
    void (*fn)();
};

inline std::vector<Case>& registry() {
    static std::vector<Case> cases;
    return cases;
}

inline int& failures() {
    static int n = 0;
    return n;
}

inline const char*& current() {
    static const char* c = "";
    return c;
}

struct Registrar {
    Registrar(const char* suite, const char* name, void (*fn)()) {
        registry().push_back({suite, name, fn});
    }
};

inline void fail(const char* file, int line, const std::string& msg) {
    std::fprintf(stderr, "  FAIL %s\n    %s:%d: %s\n", current(), file, line, msg.c_str());
    ++failures();
}

// Rendering helpers so failure output shows values, not just "false".
inline std::string show(std::string_view s) { return "\"" + std::string(s) + "\""; }
inline std::string show(const std::string& s) { return "\"" + s + "\""; }
inline std::string show(const char* s) { return std::string("\"") + s + "\""; }
inline std::string show(bool b) { return b ? "true" : "false"; }

// Scoped enums (MatchStatus, ParamKind) have no std::to_string overload, so
// they are rendered via their underlying integer.
template <typename T>
    requires std::is_enum_v<T>
inline std::string show(T v) {
    return std::to_string(static_cast<std::underlying_type_t<T>>(v));
}

template <typename T>
    requires(!std::is_enum_v<T>)
inline std::string show(T v) { return std::to_string(v); }

inline int run_all() {
    const char* last = "";
    for (const auto& c : registry()) {
        if (std::string_view(last) != c.suite) {
            std::fprintf(stderr, "[%s]\n", c.suite);
            last = c.suite;
        }
        static std::string label;
        label = std::string(c.suite) + "." + c.name;
        current() = label.c_str();
        const int before = failures();
        c.fn();
        if (failures() == before) {
            std::fprintf(stderr, "  ok   %s\n", c.name);
        }
    }
    if (failures() > 0) {
        std::fprintf(stderr, "\n%d assertion(s) failed\n", failures());
        return 1;
    }
    std::fprintf(stderr, "\nall %zu tests passed\n", registry().size());
    return 0;
}

}  // namespace aqtest

#define TEST(suite, name)                                                        \
    static void suite##_##name##_body();                                         \
    static ::aqtest::Registrar suite##_##name##_reg(#suite, #name,               \
                                                    suite##_##name##_body);      \
    static void suite##_##name##_body()

#define EXPECT_TRUE(expr)                                                        \
    do {                                                                         \
        if (!(expr)) ::aqtest::fail(__FILE__, __LINE__, "expected true: " #expr); \
    } while (0)

#define EXPECT_FALSE(expr)                                                       \
    do {                                                                         \
        if (expr) ::aqtest::fail(__FILE__, __LINE__, "expected false: " #expr);  \
    } while (0)

#define EXPECT_EQ(a, b)                                                          \
    do {                                                                         \
        auto&& _a = (a);                                                         \
        auto&& _b = (b);                                                         \
        if (!(_a == _b))                                                         \
            ::aqtest::fail(__FILE__, __LINE__,                                   \
                           std::string(#a " == " #b " (") + ::aqtest::show(_a) + \
                               " vs " + ::aqtest::show(_b) + ")");               \
    } while (0)

#define EXPECT_NE(a, b)                                                          \
    do {                                                                         \
        auto&& _a = (a);                                                         \
        auto&& _b = (b);                                                         \
        if (_a == _b)                                                            \
            ::aqtest::fail(__FILE__, __LINE__, #a " != " #b " but both are " +   \
                                                   ::aqtest::show(_a));          \
    } while (0)
