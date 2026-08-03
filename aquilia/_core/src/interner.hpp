// interner.hpp -- string -> dense uint32 id mapping.
//
// Consumer: the router's version-constraint table, which compares versions as
// integers after freeze() rather than re-parsing strings per request.
//
// Deliberately NOT used for route segments. A trie node's fan-out is 2-8, so a
// linear scan of inline string_view comparisons (a length check plus a short
// memcmp) beats hashing the segment to look up an id and then comparing ints.
// Interning only pays when the same string is compared many times against a
// large set, which is the version case, not the segment case.
//
// Phase 9C. See docs/engine/03-core-engine-design.md section 5.2.
#pragma once

#include <cstdint>
#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>

namespace aq {

/// Dense id assigned to an interned string. Ids are stable for the lifetime of
/// the Interner and are valid indices into its backing store.
using InternId = std::uint32_t;

/// Returned by lookup() when a string has never been interned.
inline constexpr InternId NO_INTERN = 0xFFFFFFFFu;

/// Append-only string table mapping byte strings to dense ids.
///
/// Byte-safe: keys may contain embedded NULs and need not be valid UTF-8. ASGI
/// servers can deliver arbitrary bytes in a request path, so every string that
/// reaches this class is treated as opaque bytes.
///
/// Not thread-safe for writes. All interning happens during lifespan startup,
/// before any request thread exists; post-freeze the router only calls lookup(),
/// which is const and safe from any thread.
class Interner {
public:
    Interner() = default;
    Interner(const Interner&) = delete;
    Interner& operator=(const Interner&) = delete;
    Interner(Interner&&) = default;
    Interner& operator=(Interner&&) = default;

    /// Return the id for @p s, assigning a new one if it is unseen.
    /// Idempotent: interning the same bytes always yields the same id.
    InternId intern(std::string_view s);

    /// Return the id for @p s, or NO_INTERN if it was never interned.
    /// Never mutates, so it is safe to call concurrently.
    [[nodiscard]] InternId lookup(std::string_view s) const noexcept;

    /// Return the bytes behind @p id. Returns an empty view if @p id is invalid.
    /// The returned view stays valid for the lifetime of the Interner.
    [[nodiscard]] std::string_view get(InternId id) const noexcept;

    [[nodiscard]] std::size_t size() const noexcept { return strings_.size(); }

private:
    // strings_ owns the bytes; map_ keys are views into that storage. Storing
    // std::string by value in a deque-like vector would invalidate those views
    // on reallocation, so the strings are held indirectly and never moved.
    std::vector<std::unique_ptr<std::string>> strings_;
    std::unordered_map<std::string_view, InternId> map_;
};

}  // namespace aq
