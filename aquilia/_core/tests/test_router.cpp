// C++ unit tests for aq::Router. Phase 9D.
#include "harness.hpp"
#include "router.hpp"

#include <string>
#include <unordered_map>

using namespace aq;

namespace {

std::unordered_map<std::string, ParamKind> kinds(
    std::initializer_list<std::pair<const char*, ParamKind>> init) {
    std::unordered_map<std::string, ParamKind> m;
    for (const auto& [k, v] : init) m.emplace(k, v);
    return m;
}

std::string value_of(const MatchResult& r, std::uint32_t i, std::string_view path) {
    return std::string(path.substr(r.params[i].value_off, r.params[i].value_len));
}

}  // namespace

TEST(Router, StaticMatchBeatsParam) {
    Router r;
    EXPECT_TRUE(r.add_static("GET", "/users/me", 1));
    EXPECT_TRUE(r.add_route("GET", "/users/<id>", kinds({{"id", ParamKind::Str}}), 2));
    r.freeze();
    EXPECT_EQ(r.match("GET", "/users/me").route_id, 1u);
    const auto m = r.match("GET", "/users/42");
    EXPECT_EQ(m.route_id, 2u);
    EXPECT_EQ(m.param_count, 1u);
    EXPECT_EQ(value_of(m, 0, "/users/42"), std::string("42"));
}

TEST(Router, BracesAreLiteralNotParams) {
    // aquilia.patterns does NOT treat {name} as a parameter: PatternCompiler
    // reports zero params for "/u/{id}" and leaves it a literal path. Registering
    // it as a param edge would make it match "/u/anything" natively while Python
    // matched only the literal text.
    Router r;
    EXPECT_TRUE(r.add_route("GET", "/u/{id}", kinds({{"id", ParamKind::Str}}), 1));
    r.freeze();
    const auto lit = r.match("GET", "/u/{id}");
    EXPECT_EQ(lit.status, MatchStatus::Hit);
    EXPECT_EQ(lit.param_count, 0u);  // matched as a literal, captured nothing
    EXPECT_EQ(r.match("GET", "/u/42").status, MatchStatus::Miss);
}

TEST(Router, ColonIsLiteralNotParam) {
    // "/u/:id" is a PatternSyntaxError in aquilia.patterns, so it can never
    // reach the native router as a param. Treated as a literal segment.
    Router r;
    EXPECT_TRUE(r.add_route("GET", "/u/:id", kinds({{"id", ParamKind::Str}}), 1));
    r.freeze();
    EXPECT_EQ(r.match("GET", "/u/:id").status, MatchStatus::Hit);
    EXPECT_EQ(r.match("GET", "/u/42").status, MatchStatus::Miss);
}

TEST(Router, StaticSegmentPreferredInsideTrie) {
    // A literal child must win over a param child at the same depth, matching
    // the Python trie's "try static child first" ordering.
    Router r;
    EXPECT_TRUE(r.add_route("GET", "/a/<x>/c", kinds({{"x", ParamKind::Str}}), 1));
    EXPECT_TRUE(r.add_route("GET", "/a/b/<y>", kinds({{"y", ParamKind::Str}}), 2));
    r.freeze();
    const auto m = r.match("GET", "/a/b/c");
    EXPECT_EQ(m.route_id, 2u);
    EXPECT_EQ(value_of(m, 0, "/a/b/c"), std::string("c"));
}

TEST(Router, DynamicIntParam) {
    Router r;
    EXPECT_TRUE(r.add_route("GET", "/items/<id:int>", kinds({{"id", ParamKind::Int}}), 7));
    r.freeze();
    const auto ok = r.match("GET", "/items/42");
    EXPECT_EQ(ok.status, MatchStatus::Hit);
    EXPECT_EQ(ok.route_id, 7u);
    EXPECT_EQ(ok.params[0].kind, ParamKind::Int);
    EXPECT_EQ(r.match("GET", "/items/-1").status, MatchStatus::Hit);
    EXPECT_EQ(r.match("GET", "/items/+7").status, MatchStatus::Hit);
}

TEST(Router, DynamicIntParamInvalid) {
    Router r;
    EXPECT_TRUE(r.add_route("GET", "/items/<id:int>", kinds({{"id", ParamKind::Int}}), 7));
    r.freeze();
    // Plainly non-numeric: a real miss, matching int() raising ValueError.
    EXPECT_EQ(r.match("GET", "/items/abc").status, MatchStatus::Miss);
    EXPECT_EQ(r.match("GET", "/items/4a").status, MatchStatus::Miss);
    EXPECT_EQ(r.match("GET", "/items/").status, MatchStatus::Miss);
}

TEST(Router, IntFormsCPythonAcceptsAreDeferred) {
    // These must NOT be reported as misses: CPython's int() accepts them, so
    // claiming a miss natively would diverge from the Python matcher.
    Router r;
    EXPECT_TRUE(r.add_route("GET", "/items/<id:int>", kinds({{"id", ParamKind::Int}}), 7));
    r.freeze();
    EXPECT_EQ(r.match("GET", "/items/1_000").status, MatchStatus::Defer);
    EXPECT_EQ(r.match("GET", "/items/ 42").status, MatchStatus::Defer);
    EXPECT_EQ(r.match("GET", "/items/\xd9\xa1").status, MatchStatus::Defer);  // U+0661
}

TEST(Router, HugeIntStillMatches) {
    // Python ints are unbounded; a 30-digit value must not be a miss just
    // because it would overflow int64. Shape-only validation, no conversion.
    Router r;
    EXPECT_TRUE(r.add_route("GET", "/items/<id:int>", kinds({{"id", ParamKind::Int}}), 7));
    r.freeze();
    EXPECT_EQ(r.match("GET", "/items/999999999999999999999999999999").status, MatchStatus::Hit);
}

TEST(Router, FloatParam) {
    Router r;
    EXPECT_TRUE(r.add_route("GET", "/m/<v:float>", kinds({{"v", ParamKind::Float}}), 3));
    r.freeze();
    EXPECT_EQ(r.match("GET", "/m/1.5").status, MatchStatus::Hit);
    EXPECT_EQ(r.match("GET", "/m/-0.25").status, MatchStatus::Hit);
    EXPECT_EQ(r.match("GET", "/m/1e10").status, MatchStatus::Hit);
    EXPECT_EQ(r.match("GET", "/m/2.").status, MatchStatus::Hit);
    EXPECT_EQ(r.match("GET", "/m/abc").status, MatchStatus::Defer);   // "inf"-shaped
    EXPECT_EQ(r.match("GET", "/m/1.2.3").status, MatchStatus::Miss);
}

TEST(Router, MultipleParams) {
    Router r;
    EXPECT_TRUE(r.add_route("GET", "/u/<uid>/p/<pid>",
                            kinds({{"uid", ParamKind::Int}, {"pid", ParamKind::Int}}), 9));
    r.freeze();
    const auto m = r.match("GET", "/u/3/p/7");
    EXPECT_EQ(m.status, MatchStatus::Hit);
    EXPECT_EQ(m.param_count, 2u);
    EXPECT_EQ(value_of(m, 0, "/u/3/p/7"), std::string("3"));
    EXPECT_EQ(value_of(m, 1, "/u/3/p/7"), std::string("7"));
}

TEST(Router, MethodIsolation) {
    Router r;
    EXPECT_TRUE(r.add_static("GET", "/x", 1));
    r.freeze();
    EXPECT_EQ(r.match("POST", "/x").status, MatchStatus::Miss);
    EXPECT_EQ(r.match("GET", "/x").route_id, 1u);
}

TEST(Router, UnknownMethodIsMiss) {
    Router r;
    EXPECT_TRUE(r.add_static("GET", "/x", 1));
    r.freeze();
    EXPECT_EQ(r.match("TRACE", "/x").status, MatchStatus::Miss);
    EXPECT_FALSE(r.add_static("TRACE", "/y", 2));
}

TEST(Router, RootPath) {
    Router r;
    EXPECT_TRUE(r.add_static("GET", "/", 1));
    r.freeze();
    EXPECT_EQ(r.match("GET", "/").route_id, 1u);
}

TEST(Router, TrailingSlashNormalisation) {
    // match_sync strips at most ONE trailing slash. "/users/" hits the static
    // entry for "/users"; "/users//" becomes "/users/" and does not.
    Router r;
    EXPECT_TRUE(r.add_static("GET", "/users", 1));
    r.freeze();
    EXPECT_EQ(r.match("GET", "/users").route_id, 1u);
    EXPECT_EQ(r.match("GET", "/users/").route_id, 1u);
    EXPECT_EQ(r.match("GET", "/users//").status, MatchStatus::Miss);
}

TEST(Router, EmptySegmentMatchesPythonSplit) {
    // "".split("/") == [""], so "" and "//" present one EMPTY segment. A route
    // whose first segment is a param therefore captures the empty string.
    Router r;
    EXPECT_TRUE(r.add_route("GET", "/<slug>", kinds({{"slug", ParamKind::Str}}), 5));
    r.freeze();
    const auto m = r.match("GET", "");
    EXPECT_EQ(m.status, MatchStatus::Hit);
    EXPECT_EQ(m.param_count, 1u);
    EXPECT_EQ(m.params[0].value_len, 0u);
}

TEST(Router, InteriorEmptySegment) {
    Router r;
    EXPECT_TRUE(r.add_route("GET", "/a/<x>/b", kinds({{"x", ParamKind::Str}}), 1));
    r.freeze();
    // "/a//b" -> segments ["a", "", "b"] -> param captures ""
    const auto m = r.match("GET", "/a//b");
    EXPECT_EQ(m.status, MatchStatus::Hit);
    EXPECT_EQ(m.params[0].value_len, 0u);
}

TEST(Router, MissOnUnregisteredPath) {
    Router r;
    EXPECT_TRUE(r.add_static("GET", "/users", 1));
    EXPECT_TRUE(r.add_route("GET", "/users/<id>", kinds({{"id", ParamKind::Str}}), 2));
    r.freeze();
    EXPECT_EQ(r.match("GET", "/nope").status, MatchStatus::Miss);
    EXPECT_EQ(r.match("GET", "/users/1/extra").status, MatchStatus::Miss);
}

TEST(Router, NonTerminalPrefixIsMiss) {
    Router r;
    EXPECT_TRUE(r.add_route("GET", "/a/b/<c>", kinds({{"c", ParamKind::Str}}), 1));
    r.freeze();
    EXPECT_EQ(r.match("GET", "/a/b").status, MatchStatus::Miss);
    EXPECT_EQ(r.match("GET", "/a").status, MatchStatus::Miss);
}

TEST(Router, ParamNameOffsetsResolve) {
    // Param name offsets index the router's own byte pool, not the path.
    Router r;
    EXPECT_TRUE(r.add_route("GET", "/u/<uid>", kinds({{"uid", ParamKind::Str}}), 1));
    r.freeze();
    const auto m = r.match("GET", "/u/bob");
    EXPECT_EQ(m.status, MatchStatus::Hit);
    EXPECT_EQ(m.params[0].name_len, 3u);
}

TEST(Router, UnknownParamNameRejected) {
    Router r;
    // "id" is absent from param_kinds -> not natively representable.
    EXPECT_FALSE(r.add_route("GET", "/x/<id>", kinds({{"other", ParamKind::Str}}), 1));
}

TEST(Router, BracedTypedSegmentIsLiteral) {
    // "{id:int}" is not param syntax in aquilia.patterns, so it registers as a
    // literal segment and matches only its own text.
    Router r;
    EXPECT_TRUE(r.add_route("GET", "/x/{id:int}", kinds({{"id", ParamKind::Int}}), 1));
    r.freeze();
    EXPECT_EQ(r.match("GET", "/x/{id:int}").route_id, 1u);
    EXPECT_EQ(r.match("GET", "/x/5").status, MatchStatus::Miss);
}

TEST(Router, AngleTypedParamAccepted) {
    Router r;
    EXPECT_TRUE(r.add_route("GET", "/x/<id:int>", kinds({{"id", ParamKind::Int}}), 1));
    r.freeze();
    EXPECT_EQ(r.match("GET", "/x/5").route_id, 1u);
}

TEST(Router, AngleUntypedParamAccepted) {
    Router r;
    EXPECT_TRUE(r.add_route("GET", "/x/<id>", kinds({{"id", ParamKind::Str}}), 1));
    r.freeze();
    EXPECT_EQ(r.match("GET", "/x/abc").route_id, 1u);
}

TEST(Router, DuplicateStaticRejected) {
    Router r;
    EXPECT_TRUE(r.add_static("GET", "/x", 1));
    EXPECT_FALSE(r.add_static("GET", "/x", 2));  // conflict -> Python path
}

TEST(Router, DuplicateTerminalRejected) {
    Router r;
    EXPECT_TRUE(r.add_route("GET", "/x/<a>", kinds({{"a", ParamKind::Str}}), 1));
    EXPECT_FALSE(r.add_route("GET", "/x/<a>", kinds({{"a", ParamKind::Str}}), 2));
}

TEST(Router, ConflictingParamKindRejected) {
    Router r;
    EXPECT_TRUE(r.add_route("GET", "/x/<a>/y", kinds({{"a", ParamKind::Int}}), 1));
    EXPECT_FALSE(r.add_route("GET", "/x/<a>/z", kinds({{"a", ParamKind::Str}}), 2));
}

TEST(Router, FreezeIsOneWay) {
    Router r;
    EXPECT_TRUE(r.add_static("GET", "/x", 1));
    r.freeze();
    EXPECT_TRUE(r.frozen());
    EXPECT_FALSE(r.add_static("GET", "/y", 2));
    EXPECT_FALSE(r.add_route("GET", "/z/<a>", kinds({{"a", ParamKind::Str}}), 3));
    r.freeze();  // idempotent
    EXPECT_EQ(r.match("GET", "/x").route_id, 1u);
}

TEST(Router, MatchBeforeFreezeIsMiss) {
    Router r;
    EXPECT_TRUE(r.add_static("GET", "/x", 1));
    EXPECT_EQ(r.match("GET", "/x").status, MatchStatus::Miss);
}

TEST(Router, TooManyParamsRejected) {
    Router r;
    std::string path;
    std::unordered_map<std::string, ParamKind> k;
    for (int i = 0; i < 20; ++i) {
        const std::string name = "p" + std::to_string(i);
        path += "/{" + name + "}";
        k.emplace(name, ParamKind::Str);
    }
    EXPECT_FALSE(r.add_route("GET", path, k, 1));
}

TEST(Router, AllowedMethods) {
    Router r;
    EXPECT_TRUE(r.add_static("GET", "/x", 1));
    EXPECT_TRUE(r.add_static("POST", "/x", 2));
    EXPECT_TRUE(r.add_route("DELETE", "/x/<id>", kinds({{"id", ParamKind::Str}}), 3));
    r.freeze();
    const auto m = r.allowed_methods("/x");
    EXPECT_EQ(m.size(), 2u);
    EXPECT_EQ(r.allowed_methods("/x/9").size(), 1u);
    EXPECT_EQ(r.allowed_methods("/nope").size(), 0u);
}

TEST(Router, ScalingTo3000Routes) {
    Router r;
    for (int i = 0; i < 3000; ++i) {
        EXPECT_TRUE(r.add_static("GET", "/route/" + std::to_string(i), static_cast<RouteId>(i)));
    }
    EXPECT_TRUE(r.add_route("GET", "/dyn/<id>", kinds({{"id", ParamKind::Int}}), 99999));
    r.freeze();
    EXPECT_EQ(r.match("GET", "/route/2999").route_id, 2999u);
    EXPECT_EQ(r.match("GET", "/dyn/5").route_id, 99999u);
    EXPECT_EQ(r.match("GET", "/route/3000").status, MatchStatus::Miss);
}

TEST(Router, DeepPathNoStackOverflow) {
    // The match walk is iterative; only freeze() recurses, and it recurses over
    // trie depth, which registration caps at MAX_PARAMS segments for params.
    Router r;
    std::string path;
    for (int i = 0; i < 200; ++i) path += "/s";
    r.freeze();
    EXPECT_EQ(r.match("GET", path).status, MatchStatus::Miss);
}

TEST(Router, ByteSafePath) {
    // ASGI can deliver arbitrary bytes; nothing may assume valid UTF-8. The
    // explicit length keeps the embedded NUL and the trailing one: the value is
    // "\xff\xfe\x00\x01\x00", 5 bytes. A NUL must not truncate the capture.
    Router r;
    EXPECT_TRUE(r.add_route("GET", "/b/<x>", kinds({{"x", ParamKind::Str}}), 1));
    r.freeze();
    const std::string path("/b/\xff\xfe\x00\x01", 8);
    EXPECT_EQ(path.size(), 8u);
    const auto m = r.match("GET", path);
    EXPECT_EQ(m.status, MatchStatus::Hit);
    EXPECT_EQ(m.params[0].value_len, 5u);
}

TEST(Router, SharedPrefixFanOut) {
    Router r;
    for (int i = 0; i < 50; ++i) {
        EXPECT_TRUE(r.add_static("GET", "/api/v1/resource" + std::to_string(i),
                                 static_cast<RouteId>(i)));
    }
    EXPECT_TRUE(r.add_route("GET", "/api/v1/x/<id>", kinds({{"id", ParamKind::Str}}), 500));
    r.freeze();
    EXPECT_EQ(r.match("GET", "/api/v1/resource7").route_id, 7u);
    EXPECT_EQ(r.match("GET", "/api/v1/x/abc").route_id, 500u);
}

int main() { return aqtest::run_all(); }
