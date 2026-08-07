// buffer.hpp -- growable output buffer with a thread-local free pool.
//
// The encoder writes JSON straight into one of these. Two properties matter:
//
//   1. No intermediate document. yyjson's mutable-doc API would need a
//      yyjson_mut_val allocated per Python object before a single byte is
//      written; for encoding that tree is pure overhead, so encode.cpp walks the
//      Python objects directly and appends here. (Decoding is the opposite case
//      -- there yyjson's immutable reader wins outright, see decode.cpp.)
//
//   2. No allocation in steady state. A server serialising a 100KB response on
//      every request should not malloc 100KB every time. Buffers are returned to
//      a thread-local pool on destruction with their capacity intact, so the
//      second request onward reuses the first request's allocation.
//
// Thread-local rather than shared: no lock, no contention, and under
// free-threaded builds no shared mutable state to reason about. The cost is one
// retained buffer per thread, capped by kMaxPooledCapacity so a single huge
// response cannot pin megabytes for the process's life.
#pragma once

#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <utility>
#include <vector>

namespace aq::json {

/// Largest capacity worth keeping in the pool, in bytes.
///
/// Above this a buffer is freed rather than retained: holding a 10MB allocation
/// per thread forever to save one malloc on a rare request is the wrong trade.
inline constexpr std::size_t kMaxPooledCapacity = 1u << 20;  // 1 MiB

/// Initial capacity for a freshly allocated buffer.
///
/// Chosen so the common small-JSON response (a few hundred bytes) never grows.
inline constexpr std::size_t kInitialCapacity = 512;

/// How many buffers a thread retains.
///
/// One is enough for the request path -- encode() finishes before the next call
/// on the same thread -- but nested encoding (a default= hook that itself
/// serialises) needs a second, so keep a small stack.
inline constexpr std::size_t kPoolDepth = 4;

/// A contiguous, growable byte buffer.
///
/// Move-only: copying an output buffer is never what the caller meant.
class Buffer {
  public:
    Buffer() = default;

    ~Buffer() { std::free(data_); }

    Buffer(const Buffer&) = delete;
    Buffer& operator=(const Buffer&) = delete;

    Buffer(Buffer&& other) noexcept
        : data_(other.data_), size_(other.size_), capacity_(other.capacity_) {
        other.data_ = nullptr;
        other.size_ = 0;
        other.capacity_ = 0;
    }

    Buffer& operator=(Buffer&& other) noexcept {
        if (this != &other) {
            std::free(data_);
            data_ = other.data_;
            size_ = other.size_;
            capacity_ = other.capacity_;
            other.data_ = nullptr;
            other.size_ = 0;
            other.capacity_ = 0;
        }
        return *this;
    }

    /// Bytes written so far.
    [[nodiscard]] std::size_t size() const noexcept { return size_; }

    /// Allocated capacity.
    [[nodiscard]] std::size_t capacity() const noexcept { return capacity_; }

    /// Pointer to the written bytes. Not NUL-terminated.
    [[nodiscard]] const char* data() const noexcept { return data_; }

    /// Discard the contents, keeping the allocation.
    void clear() noexcept { size_ = 0; }

    /// Ensure room for `extra` more bytes.
    ///
    /// @returns false on allocation failure; the buffer is unchanged and the
    ///          caller must abort. No exception is thrown -- this is the request
    ///          hot path and an exception costs more than the whole encode.
    [[nodiscard]] bool reserve_extra(std::size_t extra) noexcept {
        const std::size_t needed = size_ + extra;
        if (needed <= capacity_) return true;
        return grow(needed);
    }

    /// Append one byte. Caller must have reserved space.
    void put_unchecked(char c) noexcept { data_[size_++] = c; }

    /// Append one byte, growing if needed.
    [[nodiscard]] bool put(char c) noexcept {
        if (size_ == capacity_ && !grow(size_ + 1)) return false;
        data_[size_++] = c;
        return true;
    }

    /// Append `n` bytes from `src`, growing if needed.
    [[nodiscard]] bool append(const char* src, std::size_t n) noexcept {
        if (!reserve_extra(n)) return false;
        std::memcpy(data_ + size_, src, n);
        size_ += n;
        return true;
    }

    /// Append a NUL-terminated literal, growing if needed.
    template <std::size_t N>
    [[nodiscard]] bool append_literal(const char (&lit)[N]) noexcept {
        return append(lit, N - 1);
    }

    /// Writable pointer to `n` reserved bytes, for callers that format in place
    /// (integer and float conversion). Advance with commit().
    [[nodiscard]] char* reserve_raw(std::size_t n) noexcept {
        if (!reserve_extra(n)) return nullptr;
        return data_ + size_;
    }

    /// Record `n` bytes written via reserve_raw().
    void commit(std::size_t n) noexcept { size_ += n; }

    /// Drop the last byte. Used to erase a trailing separator.
    void pop_back() noexcept {
        if (size_ > 0) --size_;
    }

  private:
    /// Grow to at least `needed`, doubling to keep appends amortised O(1).
    [[nodiscard]] bool grow(std::size_t needed) noexcept {
        std::size_t next = capacity_ ? capacity_ : kInitialCapacity;
        while (next < needed) {
            // Guard against overflow on a pathological size request.
            if (next > (SIZE_MAX >> 1)) return false;
            next <<= 1;
        }
        char* fresh = static_cast<char*>(std::realloc(data_, next));
        if (!fresh) return false;
        data_ = fresh;
        capacity_ = next;
        return true;
    }

    char* data_ = nullptr;
    std::size_t size_ = 0;
    std::size_t capacity_ = 0;
};

/// RAII handle that takes a Buffer from the thread-local pool and returns it.
///
/// Usage:
///     PooledBuffer buf;
///     buf->append(...);
///
/// The buffer is cleared on acquisition, so a caller never sees another
/// request's bytes.
class PooledBuffer {
  public:
    PooledBuffer() noexcept : buf_(acquire()) { buf_.clear(); }

    ~PooledBuffer() { release(std::move(buf_)); }

    PooledBuffer(const PooledBuffer&) = delete;
    PooledBuffer& operator=(const PooledBuffer&) = delete;

    Buffer* operator->() noexcept { return &buf_; }
    Buffer& operator*() noexcept { return buf_; }

  private:
    /// The thread's free list. Function-local static so there is no
    /// initialisation-order dependency across translation units.
    static std::vector<Buffer>& pool() noexcept {
        thread_local std::vector<Buffer> p;
        return p;
    }

    static Buffer acquire() noexcept {
        auto& p = pool();
        if (p.empty()) return Buffer{};
        Buffer b = std::move(p.back());
        p.pop_back();
        return b;
    }

    static void release(Buffer&& b) noexcept {
        if (b.capacity() == 0 || b.capacity() > kMaxPooledCapacity) return;
        auto& p = pool();
        if (p.size() >= kPoolDepth) return;
        b.clear();
        p.push_back(std::move(b));
    }

    Buffer buf_;
};

}  // namespace aq::json
