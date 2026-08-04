#include "uuid_parse.hpp"

namespace aq {
namespace {

// 256-entry hex classifier. Anything not explicitly a hex digit -- underscore,
// '+', space, '{', any byte >= 0x80 from a UTF-8 sequence -- is rejected, so
// the non-ASCII and separator rejections fall out of the same table lookup.
constexpr auto make_hex_table() {
    struct Table {
        bool v[256];
    };
    Table t{};
    for (int i = 0; i < 256; ++i) t.v[i] = false;
    for (int i = '0'; i <= '9'; ++i) t.v[i] = true;
    for (int i = 'a'; i <= 'f'; ++i) t.v[i] = true;
    for (int i = 'A'; i <= 'F'; ++i) t.v[i] = true;
    return t;
}

constexpr auto kIsHex = make_hex_table();

inline bool is_hex(char c) noexcept { return kIsHex.v[static_cast<unsigned char>(c)]; }

// Copy `n` hex digits, rejecting the first non-hex byte.
inline bool copy_hex(const char* src, char* dst, int n) noexcept {
    for (int i = 0; i < n; ++i) {
        const char c = src[i];
        if (!is_hex(c)) return false;
        dst[i] = c;
    }
    return true;
}

}  // namespace

bool normalise_uuid_hex(std::string_view s, char out[kUuidHexBufSize]) noexcept {
    // Strip an exact lowercase "urn:uuid:" prefix. CPython removes every
    // occurrence of "urn:" and "uuid:" anywhere in the string; matching only
    // the canonical prefix means unusual placements fall through to Python
    // rather than being parsed differently here.
    if (s.size() >= 9 && s.compare(0, 9, "urn:uuid:") == 0) {
        s.remove_prefix(9);
    }

    // Strip one balanced brace pair. CPython uses strip('{}'), which removes
    // any number of either character from either end; only the balanced single
    // pair is handled here for the same reason.
    if (s.size() >= 2 && s.front() == '{' && s.back() == '}') {
        s.remove_prefix(1);
        s.remove_suffix(1);
    }

    if (s.size() == 32) {
        if (!copy_hex(s.data(), out, 32)) return false;
        out[32] = '\0';
        return true;
    }

    if (s.size() == 36) {
        const char* p = s.data();
        // Hyphens must sit at exactly the canonical 8-4-4-4-12 offsets.
        if (p[8] != '-' || p[13] != '-' || p[18] != '-' || p[23] != '-') return false;
        if (!copy_hex(p + 0, out + 0, 8)) return false;
        if (!copy_hex(p + 9, out + 8, 4)) return false;
        if (!copy_hex(p + 14, out + 12, 4)) return false;
        if (!copy_hex(p + 19, out + 16, 4)) return false;
        if (!copy_hex(p + 24, out + 20, 12)) return false;
        out[32] = '\0';
        return true;
    }

    return false;
}

}  // namespace aq
