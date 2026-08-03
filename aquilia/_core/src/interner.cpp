#include "interner.hpp"

#include <memory>

namespace aq {

InternId Interner::intern(std::string_view s) {
    if (const auto it = map_.find(s); it != map_.end()) {
        return it->second;
    }
    // Own the bytes first, then key the map by a view into that owned copy --
    // never by the caller's view, which may dangle the moment we return.
    auto owned = std::make_unique<std::string>(s);
    const std::string_view key{*owned};
    const auto id = static_cast<InternId>(strings_.size());
    strings_.push_back(std::move(owned));
    map_.emplace(key, id);
    return id;
}

InternId Interner::lookup(std::string_view s) const noexcept {
    const auto it = map_.find(s);
    return it == map_.end() ? NO_INTERN : it->second;
}

std::string_view Interner::get(InternId id) const noexcept {
    if (id >= strings_.size()) {
        return {};
    }
    return *strings_[id];
}

}  // namespace aq
