#include "router.hpp"

#include <cctype>
#include <cstring>

namespace aq {
namespace {

// Method table order defines the dense index. Matches the methods the Python
// router registers; anything else (TRACE, CONNECT, extensions) is not native.
constexpr std::string_view kMethods[N_METHODS] = {
    "GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", "WS", "WEBSOCKET",
};

/// Split a normalised path into segments, reproducing exactly:
///     path.strip("/").split("/") if path != "/" else []
///
/// The empty-segment behaviour is load-bearing. Python's "".split("/") yields
/// [""] -- one empty segment, not zero -- so "" and "//" must produce a single
/// empty segment here too, or the native and Python matchers diverge on those
/// inputs. tests/test_router.cpp pins this.
void split_segments(std::string_view path, std::vector<std::string_view>& out) {
    out.clear();
    if (path == "/") {
        return;
    }
    // strip("/") removes leading AND trailing runs of '/'
    std::size_t b = 0;
    std::size_t e = path.size();
    while (b < e && path[b] == '/') ++b;
    while (e > b && path[e - 1] == '/') --e;
    const std::string_view core = path.substr(b, e - b);
    if (core.empty()) {
        out.emplace_back();  // "".split("/") == [""]
        return;
    }
    std::size_t start = 0;
    while (true) {
        const std::size_t slash = core.find('/', start);
        if (slash == std::string_view::npos) {
            out.push_back(core.substr(start));
            break;
        }
        out.push_back(core.substr(start, slash - start));
        start = slash + 1;
    }
}

/// Extract a param name from a segment.
///
/// ONLY `<name>` and `<name:type>` are parameters. This is not a stylistic
/// choice -- it is what aquilia.patterns actually parses. Verified against
/// PatternCompiler:
///
///     "/u/<id:int>"  -> params ['id']    (a real parameter)
///     "/u/{id}"      -> params []        (a LITERAL path containing braces)
///     "/u/:id"       -> PatternSyntaxError
///
/// Treating `{id}` or `:id` as a param here would register a literal route as a
/// param edge, so "/u/{id}" would match "/u/anything" natively while Python
/// matched only the literal text. tests/engine/test_router_parity.py pins this.
///
/// Splat segments (`*rest`) compile to a `path` param, which is not a native
/// param kind, so those routes are rejected on the Python side before reaching
/// here and need no handling in this function.
bool param_name_of(std::string_view seg, std::string_view& name) {
    if (seg.size() >= 2 && seg.front() == '<' && seg.back() == '>') {
        const std::string_view inner = seg.substr(1, seg.size() - 2);
        const std::size_t colon = inner.find(':');
        name = colon == std::string_view::npos ? inner : inner.substr(0, colon);
        return true;
    }
    return false;
}

/// Strip at most one trailing slash, reproducing match_sync's normalisation:
///     path[:-1] if len(path) > 1 and path[-1] == "/" else path
///
/// Deliberately different from registration, which uses rstrip("/") (all
/// trailing slashes). That asymmetry exists in the Python router and is
/// preserved: "/users//" normalises to "/users/", which is not the registered
/// "/users", so it misses tier 1 and falls to the trie.
std::string_view normalise(std::string_view path) noexcept {
    if (path.size() > 1 && path.back() == '/') {
        return path.substr(0, path.size() - 1);
    }
    return path;
}

/// Does this segment lie inside CPython's int() ASCII fast path?
///
/// Accepts optional single +/- then one or more ASCII digits. Everything else --
/// underscores ("1_000"), surrounding whitespace, unicode decimal digits
/// (U+0660 et al), empty -- is Defer, not Miss: CPython accepts several of
/// those and the native matcher must not claim a miss where Python would match.
bool ascii_int_shape(std::string_view s, bool& deferrable) noexcept {
    deferrable = false;
    std::size_t i = 0;
    if (i < s.size() && (s[i] == '+' || s[i] == '-')) ++i;
    if (i >= s.size()) {
        // "" / "+" / "-": int() raises ValueError -> a real miss, no defer.
        return false;
    }
    for (; i < s.size(); ++i) {
        const unsigned char c = static_cast<unsigned char>(s[i]);
        if (c >= '0' && c <= '9') continue;
        if (c == '_' || c > 0x7F || c == ' ' || c == '\t' || c == '\n' || c == '\r' ||
            c == '\f' || c == '\v') {
            deferrable = true;  // CPython might accept; let Python decide
            return false;
        }
        return false;  // plainly not an integer
    }
    return true;
}

/// Digits-and-shape check for float(). Conservative: only plain decimal forms
/// with an optional exponent take the native path. "inf", "nan", "1_0",
/// hex floats, and whitespace-padded forms defer to Python.
bool ascii_float_shape(std::string_view s, bool& deferrable) noexcept {
    deferrable = false;
    std::size_t i = 0;
    if (i < s.size() && (s[i] == '+' || s[i] == '-')) ++i;
    bool any_digit = false;
    while (i < s.size() && s[i] >= '0' && s[i] <= '9') { ++i; any_digit = true; }
    if (i < s.size() && s[i] == '.') {
        ++i;
        while (i < s.size() && s[i] >= '0' && s[i] <= '9') { ++i; any_digit = true; }
    }
    if (!any_digit) {
        // Could be "inf"/"nan"/unicode; float() may accept -> defer.
        for (const char c : s) {
            if (static_cast<unsigned char>(c) > 0x7F || std::isalpha(static_cast<unsigned char>(c))) {
                deferrable = true;
                break;
            }
        }
        return false;
    }
    if (i < s.size() && (s[i] == 'e' || s[i] == 'E')) {
        ++i;
        if (i < s.size() && (s[i] == '+' || s[i] == '-')) ++i;
        bool exp_digit = false;
        while (i < s.size() && s[i] >= '0' && s[i] <= '9') { ++i; exp_digit = true; }
        if (!exp_digit) return false;
    }
    if (i != s.size()) {
        for (std::size_t j = i; j < s.size(); ++j) {
            const unsigned char c = static_cast<unsigned char>(s[j]);
            if (c == '_' || c > 0x7F || std::isspace(c)) {
                deferrable = true;
                break;
            }
        }
        return false;
    }
    return true;
}

}  // namespace

std::size_t method_index(std::string_view method) noexcept {
    for (std::size_t i = 0; i < N_METHODS; ++i) {
        if (kMethods[i] == method) return i;
    }
    return N_METHODS;
}

std::size_t Router::static_count() const noexcept {
    std::size_t n = 0;
    for (const auto& m : static_) n += m.size();
    return n;
}

bool Router::add_static(std::string_view method, std::string_view path, RouteId route_id) {
    if (frozen_) return false;
    const std::size_t midx = method_index(method);
    if (midx == N_METHODS) return false;
    auto& map = static_[midx];
    const std::string key{path};
    if (map.find(key) != map.end()) {
        return false;  // conflict: caller keeps the method on the Python path
    }
    map.emplace(key, route_id);
    return true;
}

std::uint32_t Router::build_root(std::size_t midx) {
    if (build_roots_[midx] == NO_NODE) {
        build_roots_[midx] = static_cast<std::uint32_t>(build_.size());
        build_.emplace_back();
    }
    return build_roots_[midx];
}

bool Router::add_route(std::string_view method, std::string_view path,
                       const std::unordered_map<std::string, ParamKind>& param_kinds,
                       RouteId route_id) {
    if (frozen_) return false;
    const std::size_t midx = method_index(method);
    if (midx == N_METHODS) return false;

    // Registration normalisation is rstrip("/") -- all trailing slashes -- to
    // match _trie_insert's `route.full_path.rstrip("/") or "/"`.
    std::size_t e = path.size();
    while (e > 0 && path[e - 1] == '/') --e;
    const std::string_view raw = e == 0 ? std::string_view{"/"} : path.substr(0, e);

    std::vector<std::string_view> segs;
    split_segments(raw, segs);
    if (segs.size() > MatchResult::MAX_PARAMS) {
        // Deep paths are rare; refusing them keeps match() allocation-free.
        return false;
    }

    std::uint32_t cur = build_root(midx);
    std::uint32_t nparams = 0;
    for (const std::string_view seg : segs) {
        std::string_view pname;
        if (param_name_of(seg, pname)) {
            const auto it = param_kinds.find(std::string{pname});
            if (it == param_kinds.end()) {
                return false;  // unknown param -> not natively representable
            }
            if (++nparams > MatchResult::MAX_PARAMS) return false;
            if (build_[cur].param_child == NO_NODE) {
                const auto child = static_cast<std::uint32_t>(build_.size());
                build_.emplace_back();
                build_[cur].param_child = child;
                build_[child].param_name = std::string{pname};
                build_[child].param_kind = it->second;
            } else {
                // A second param name or kind at the same position cannot be
                // represented (the Python trie also keeps only the first).
                const auto& existing = build_[build_[cur].param_child];
                if (existing.param_name != pname || existing.param_kind != it->second) {
                    return false;
                }
            }
            cur = build_[cur].param_child;
        } else {
            const std::string key{seg};
            const auto it = build_[cur].children.find(key);
            if (it == build_[cur].children.end()) {
                const auto child = static_cast<std::uint32_t>(build_.size());
                build_.emplace_back();
                build_[cur].children.emplace(key, child);
                cur = child;
            } else {
                cur = it->second;
            }
        }
    }

    if (build_[cur].route_id != NO_ROUTE) {
        return false;  // duplicate terminal -> conflict, stay on Python path
    }
    build_[cur].route_id = route_id;
    return true;
}

void Router::fill(std::uint32_t dest, std::uint32_t build_idx, std::string_view seg) {
    // Index-based, and every append to seg_bytes_ happens after its offset is
    // read. Holding a Node& across a nodes_ append would dangle -- that bug cost
    // every parameterised route a broken param link, so this stays index-only.
    const auto seg_off = static_cast<std::uint32_t>(seg_bytes_.size());
    seg_bytes_.append(seg);
    std::uint32_t pname_off = 0;
    std::uint32_t pname_len = 0;
    const BuildNode& b = build_[build_idx];
    if (!b.param_name.empty()) {
        pname_off = static_cast<std::uint32_t>(seg_bytes_.size());
        pname_len = static_cast<std::uint32_t>(b.param_name.size());
        seg_bytes_.append(b.param_name);
    }
    Node& n = nodes_[dest];
    n.seg_off = seg_off;
    n.seg_len = static_cast<std::uint32_t>(seg.size());
    n.param_name_off = pname_off;
    n.param_name_len = pname_len;
    n.param_kind = b.param_kind;
    n.route_id = b.route_id;
}

void Router::freeze() {
    if (frozen_) return;
    seg_bytes_.reserve(1024);

    // Breadth-first, so a node's children land in one contiguous run and
    // find_child walks adjacent cache lines. Iterative: freeze() must not
    // recurse over trie depth, which is attacker-influenced via path length.
    struct Pending {
        std::uint32_t build_idx;
        std::uint32_t dest_idx;
    };
    std::vector<Pending> queue;

    for (std::size_t m = 0; m < N_METHODS; ++m) {
        if (build_roots_[m] == NO_NODE) continue;
        const auto root_dest = static_cast<std::uint32_t>(nodes_.size());
        nodes_.emplace_back();
        fill(root_dest, build_roots_[m], {});
        roots_[m] = root_dest;

        queue.clear();
        queue.push_back({build_roots_[m], root_dest});
        for (std::size_t qi = 0; qi < queue.size(); ++qi) {
            const Pending cur = queue[qi];  // by value: queue grows below
            const auto child_count =
                static_cast<std::uint32_t>(build_[cur.build_idx].children.size());

            std::uint32_t first_child = NO_NODE;
            if (child_count > 0) {
                first_child = static_cast<std::uint32_t>(nodes_.size());
                nodes_.resize(nodes_.size() + child_count);
                std::uint32_t slot = first_child;
                // children is a std::map, so iteration order is deterministic
                // and two identical route tables flatten identically.
                for (const auto& [key, cidx] : build_[cur.build_idx].children) {
                    fill(slot, cidx, key);
                    queue.push_back({cidx, slot});
                    ++slot;
                }
            }

            std::uint32_t param_idx = NO_NODE;
            if (build_[cur.build_idx].param_child != NO_NODE) {
                param_idx = static_cast<std::uint32_t>(nodes_.size());
                nodes_.emplace_back();
                fill(param_idx, build_[cur.build_idx].param_child, {});
                queue.push_back({build_[cur.build_idx].param_child, param_idx});
            }

            Node& n = nodes_[cur.dest_idx];
            n.first_child = first_child;
            n.child_count = child_count;
            n.param_child = param_idx;
        }
    }

    build_.clear();
    build_.shrink_to_fit();
    frozen_ = true;
}

const Router::Node* Router::find_child(const Node& parent, std::string_view seg) const noexcept {
    // Linear scan over a contiguous run. Fan-out is small (2-8 in practice), so
    // this beats hashing per node -- length check first, memcmp only on a match.
    const std::uint32_t end = parent.first_child + parent.child_count;
    for (std::uint32_t i = parent.first_child; i < end; ++i) {
        const Node& c = nodes_[i];
        if (c.seg_len == seg.size() &&
            std::memcmp(seg_bytes_.data() + c.seg_off, seg.data(), seg.size()) == 0) {
            return &c;
        }
    }
    return nullptr;
}

MatchResult Router::match(std::string_view method, std::string_view path) const noexcept {
    MatchResult r;
    if (!frozen_) return r;
    const std::size_t midx = method_index(method);
    if (midx == N_METHODS) return r;

    const std::string_view norm = normalise(path);

    // -- Tier 1: exact static path --
    const auto& smap = static_[midx];
    if (!smap.empty()) {
        // Transparent lookup: probes with the view, no std::string constructed.
        const auto it = smap.find(norm);
        if (it != smap.end()) {
            r.status = MatchStatus::Hit;
            r.route_id = it->second;
            return r;
        }
    }

    // -- Tier 2: trie walk --
    const std::uint32_t root = roots_[midx];
    if (root == NO_NODE) return r;

    // Inline segment walk: no split, no allocation, views into `path`.
    std::size_t b = 0;
    std::size_t e = norm.size();
    while (b < e && norm[b] == '/') ++b;
    while (e > b && norm[e - 1] == '/') --e;

    const Node* node = &nodes_[root];
    std::uint32_t nparams = 0;

    if (norm != "/") {
        const std::string_view core = norm.substr(b, e - b);
        // Mirrors "".split("/") == [""]: an empty core is one empty segment.
        // `start > core.size()` is the loop's termination condition, so the
        // empty-core case runs the body exactly once with an empty segment.
        std::size_t start = 0;
        while (start <= core.size()) {
            const std::size_t slash = core.find('/', start);
            const std::size_t seg_end = slash == std::string_view::npos ? core.size() : slash;
            const std::string_view seg = core.substr(start, seg_end - start);
            const std::size_t seg_off = b + start;
            start = seg_end + 1;  // past-the-end after the final segment

            if (const Node* child = find_child(*node, seg)) {
                node = child;
            } else if (node->param_child != NO_NODE) {
                const Node& p = nodes_[node->param_child];
                if (nparams >= MatchResult::MAX_PARAMS) return r;
                // Validate the shape now; build Python objects only on a hit.
                if (p.param_kind == ParamKind::Int) {
                    bool deferrable = false;
                    if (!ascii_int_shape(seg, deferrable)) {
                        if (deferrable) { r.status = MatchStatus::Defer; }
                        return r;
                    }
                } else if (p.param_kind == ParamKind::Float) {
                    bool deferrable = false;
                    if (!ascii_float_shape(seg, deferrable)) {
                        if (deferrable) { r.status = MatchStatus::Defer; }
                        return r;
                    }
                }
                CapturedParam& cp = r.params[nparams++];
                cp.name_off = p.param_name_off;
                cp.name_len = p.param_name_len;
                cp.value_off = static_cast<std::uint32_t>(seg_off);
                cp.value_len = static_cast<std::uint32_t>(seg.size());
                cp.kind = p.param_kind;
                node = &p;
            } else {
                return r;  // miss: zero allocations performed
            }
        }
    }

    if (node->route_id == NO_ROUTE) return r;
    r.status = MatchStatus::Hit;
    r.route_id = node->route_id;
    r.param_count = nparams;
    // Param name offsets index seg_bytes_; value offsets index `path`. The
    // binding layer knows which buffer each belongs to.
    return r;
}

std::vector<std::string_view> Router::allowed_methods(std::string_view path) const {
    std::vector<std::string_view> out;
    if (!frozen_) return out;
    for (std::size_t i = 0; i < N_METHODS; ++i) {
        const MatchResult r = match(kMethods[i], path);
        if (r.status == MatchStatus::Hit) {
            out.push_back(kMethods[i]);
        }
    }
    return out;
}

}  // namespace aq
