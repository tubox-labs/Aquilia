// router.hpp -- radix trie over path segments, flattened for cache locality.
//
// Replaces the constant-factor Python overhead in ControllerRouter.match_sync
// tiers 1 and 2 (static hash map, segment trie). Tier 3 (regex) stays in Python
// and is never reached natively -- see docs/engine/05-routing-engine-spec.md s4.
//
// Scope boundary: this class matches paths and nothing else. It holds no
// version constraints, no query-param metadata, no validators, and no Python
// callables. The Python layer decides per-method whether native matching is
// even applicable (ControllerRouter._native_eligible) and keeps full ownership
// of route objects -- the native side sees only dense uint32 route ids.
//
// Phase 9D.
#pragma once

#include <cstdint>
#include <map>
#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>

namespace aq {

/// Transparent hash/equality so the static map can be probed with a
/// string_view. Without is_transparent, every lookup would construct a
/// std::string -- a heap allocation on the hottest path in the router.
struct SvHash {
    using is_transparent = void;
    using transparent_key_equal = std::equal_to<>;
    [[nodiscard]] std::size_t operator()(std::string_view s) const noexcept {
        return std::hash<std::string_view>{}(s);
    }
};

using RouteId = std::uint32_t;

inline constexpr RouteId NO_ROUTE = 0xFFFFFFFFu;
inline constexpr std::uint32_t NO_NODE = 0xFFFFFFFFu;

/// Conversion applied to a captured path segment.
///
/// Only these three exist natively. UUID, slug, and catch-all `path` params, and
/// any param carrying validators, make their whole method ineligible on the
/// Python side -- the native router never sees them. Adding a kind here without
/// also relaxing that eligibility check would silently change behaviour.
enum class ParamKind : std::uint8_t {
    Str = 0,
    Int = 1,
    Float = 2,
};

/// Outcome of a match attempt.
enum class MatchStatus : std::uint8_t {
    /// Definitive miss: no route in this method's table can accept the path.
    Miss = 0,
    /// Matched: route_id is set and params holds the captured segments.
    Hit = 1,
    /// Native matching cannot decide this path -- the caller must fall back to
    /// the Python matcher. Raised only for param values whose textual form is
    /// outside the strict ASCII fast path (unicode digits, `1_000`, whitespace,
    /// `inf`), where CPython's int()/float() semantics are the authority.
    Defer = 2,
};

/// A captured param, as offsets into the caller's path buffer.
///
/// Offsets rather than strings: on a miss no Python object and no heap
/// allocation is produced at all, which is what makes the miss path cheap.
struct CapturedParam {
    std::uint32_t name_off;
    std::uint32_t name_len;
    std::uint32_t value_off;
    std::uint32_t value_len;
    ParamKind kind;
};

/// Result of match(). Params are only meaningful when status == Hit.
struct MatchResult {
    MatchStatus status = MatchStatus::Miss;
    RouteId route_id = NO_ROUTE;
    std::uint32_t param_count = 0;
    // 16 params is far beyond any real route; deeper paths fall back to Python
    // rather than growing this, so the hot path never allocates.
    static constexpr std::uint32_t MAX_PARAMS = 16;
    CapturedParam params[MAX_PARAMS];
};

/// Number of HTTP methods indexed by the fixed-size root array.
inline constexpr std::size_t N_METHODS = 9;

/// Map an HTTP method name to a dense index, or N_METHODS if unrecognised.
[[nodiscard]] std::size_t method_index(std::string_view method) noexcept;

/// Radix trie router with a static-path fast path.
///
/// Lifecycle: construct -> add_static/add_route* -> freeze() -> match()*.
/// freeze() is one-way. Post-freeze the router is immutable, so match() is
/// lock-free and callable from any thread without synchronisation.
class Router {
public:
    Router() = default;
    Router(const Router&) = delete;
    Router& operator=(const Router&) = delete;

    /// Register a parameter-free path for O(1) exact lookup.
    /// Returns false if this (method, path) is already registered -- the caller
    /// treats that as a route conflict and keeps the method on the Python path
    /// so the existing RoutingFault is raised unchanged.
    bool add_static(std::string_view method, std::string_view path, RouteId route_id);

    /// Register a parameterised path in the trie.
    ///
    /// @param param_kinds Kind for each param name appearing in @p path.
    /// @return false if the path is not natively representable (unknown method,
    ///         a param name absent from @p param_kinds, too many params, or a
    ///         duplicate terminal). A false return means the caller must keep
    ///         the whole method on the Python path.
    bool add_route(std::string_view method, std::string_view path,
                   const std::unordered_map<std::string, ParamKind>& param_kinds,
                   RouteId route_id);

    /// Flatten the trie into contiguous arrays. Idempotent.
    void freeze();

    [[nodiscard]] bool frozen() const noexcept { return frozen_; }

    /// Match @p path. Requires frozen(); returns Miss otherwise.
    ///
    /// @p path is used only for the duration of the call: the returned offsets
    /// index into it and no view is retained.
    [[nodiscard]] MatchResult match(std::string_view method, std::string_view path) const noexcept;

    /// Methods that have at least one route accepting @p path. Used only on the
    /// 405 path, where an allocation is irrelevant.
    [[nodiscard]] std::vector<std::string_view> allowed_methods(std::string_view path) const;

    [[nodiscard]] std::size_t node_count() const noexcept { return nodes_.size(); }
    [[nodiscard]] std::size_t static_count() const noexcept;

    /// Byte pool that CapturedParam::name_off indexes. Param *values* index the
    /// caller's path buffer instead -- the two offsets are not interchangeable.
    [[nodiscard]] std::string_view name_bytes() const noexcept { return seg_bytes_; }

private:
    /// Mutable trie node, used during registration only.
    struct BuildNode {
        std::map<std::string, std::uint32_t> children;  // ordered: deterministic flatten
        std::uint32_t param_child = NO_NODE;
        std::string param_name;
        ParamKind param_kind = ParamKind::Str;
        RouteId route_id = NO_ROUTE;
    };

    /// Flattened node. Children of a node occupy [first_child, +child_count)
    /// so a segment scan walks adjacent cache lines.
    struct Node {
        std::uint32_t first_child = NO_NODE;
        std::uint32_t child_count = 0;
        std::uint32_t seg_off = 0;   // this node's own literal segment
        std::uint32_t seg_len = 0;
        std::uint32_t param_child = NO_NODE;
        std::uint32_t param_name_off = 0;
        std::uint32_t param_name_len = 0;
        RouteId route_id = NO_ROUTE;
        ParamKind param_kind = ParamKind::Str;
    };

    std::uint32_t build_root(std::size_t midx);
    /// Populate the already-allocated node @p dest from build node @p build_idx.
    void fill(std::uint32_t dest, std::uint32_t build_idx, std::string_view seg);
    [[nodiscard]] const Node* find_child(const Node& parent, std::string_view seg) const noexcept;

    // -- registration state (discarded by freeze) --
    std::vector<BuildNode> build_;
    std::uint32_t build_roots_[N_METHODS] = {NO_NODE, NO_NODE, NO_NODE, NO_NODE, NO_NODE,
                                            NO_NODE, NO_NODE, NO_NODE, NO_NODE};

    // -- frozen state --
    std::vector<Node> nodes_;
    std::string seg_bytes_;  // all segment and param-name bytes, contiguous
    std::uint32_t roots_[N_METHODS] = {NO_NODE, NO_NODE, NO_NODE, NO_NODE, NO_NODE,
                                      NO_NODE, NO_NODE, NO_NODE, NO_NODE};
    std::unordered_map<std::string, RouteId, SvHash, std::equal_to<>> static_[N_METHODS];
    bool frozen_ = false;
};

}  // namespace aq
