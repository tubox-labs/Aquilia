// test_buffer.cpp -- the growable buffer and its thread-local pool.
//
// The buffer is where every encoded byte lands, so a bug here corrupts output
// rather than merely slowing it down. The pool is the reason a server stops
// allocating after the first response of a given size, which makes "capacity
// survives, contents do not" the property most worth pinning.
#include <cstring>
#include <string>
#include <thread>
#include <vector>

#include "buffer.hpp"
#include "harness.hpp"

using aq::json::Buffer;
using aq::json::kMaxPooledCapacity;
using aq::json::PooledBuffer;

namespace {

std::string contents(const Buffer& b) { return std::string(b.data(), b.size()); }

}  // namespace

// ---------------------------------------------------------------------------
// Buffer
// ---------------------------------------------------------------------------

TEST(Buffer, StartsEmpty) {
    Buffer b;
    EXPECT_EQ(b.size(), std::size_t{0});
}

TEST(Buffer, PutAppends) {
    Buffer b;
    EXPECT_TRUE(b.put('a'));
    EXPECT_TRUE(b.put('b'));
    EXPECT_EQ(contents(b), "ab");
}

TEST(Buffer, AppendCopies) {
    Buffer b;
    EXPECT_TRUE(b.append("hello", 5));
    EXPECT_EQ(contents(b), "hello");
}

TEST(Buffer, AppendLiteralExcludesNul) {
    Buffer b;
    EXPECT_TRUE(b.append_literal("null"));
    EXPECT_EQ(b.size(), std::size_t{4});
    EXPECT_EQ(contents(b), "null");
}

TEST(Buffer, GrowsBeyondInitialCapacity) {
    Buffer b;
    const std::string big(100000, 'x');
    EXPECT_TRUE(b.append(big.data(), big.size()));
    EXPECT_EQ(b.size(), big.size());
    EXPECT_EQ(contents(b), big);
}

TEST(Buffer, ManySmallAppendsPreserveOrder) {
    Buffer b;
    std::string expected;
    for (int i = 0; i < 5000; ++i) {
        const char c = static_cast<char>('a' + (i % 26));
        EXPECT_TRUE(b.put(c));
        expected.push_back(c);
    }
    EXPECT_EQ(contents(b), expected);
}

TEST(Buffer, ClearKeepsCapacity) {
    Buffer b;
    EXPECT_TRUE(b.append(std::string(1000, 'x').data(), 1000));
    const std::size_t cap = b.capacity();
    b.clear();
    EXPECT_EQ(b.size(), std::size_t{0});
    EXPECT_EQ(b.capacity(), cap);
}

TEST(Buffer, ReserveRawAndCommit) {
    Buffer b;
    char* dst = b.reserve_raw(4);
    EXPECT_TRUE(dst != nullptr);
    std::memcpy(dst, "1234", 4);
    b.commit(4);
    EXPECT_EQ(contents(b), "1234");
}

TEST(Buffer, ReserveRawDoesNotChangeSizeUntilCommit) {
    Buffer b;
    EXPECT_TRUE(b.append("ab", 2));
    (void)b.reserve_raw(64);
    EXPECT_EQ(b.size(), std::size_t{2});
}

TEST(Buffer, PopBack) {
    Buffer b;
    EXPECT_TRUE(b.append("ab,", 3));
    b.pop_back();
    EXPECT_EQ(contents(b), "ab");
}

TEST(Buffer, PopBackOnEmptyIsSafe) {
    Buffer b;
    b.pop_back();
    EXPECT_EQ(b.size(), std::size_t{0});
}

TEST(Buffer, MoveTransfersOwnership) {
    Buffer a;
    EXPECT_TRUE(a.append("data", 4));
    Buffer moved(std::move(a));
    EXPECT_EQ(contents(moved), "data");
    EXPECT_EQ(a.size(), std::size_t{0});
    EXPECT_EQ(a.capacity(), std::size_t{0});
}

TEST(Buffer, MoveAssignReleasesTarget) {
    Buffer a;
    EXPECT_TRUE(a.append("new", 3));
    Buffer b;
    EXPECT_TRUE(b.append("old-and-longer", 14));
    b = std::move(a);
    EXPECT_EQ(contents(b), "new");
}

TEST(Buffer, EmbeddedNulsArePreserved) {
    // JSON strings may contain NUL (escaped on the way out), so the buffer must
    // be length-tracked rather than NUL-terminated.
    Buffer b;
    EXPECT_TRUE(b.append("a\0b", 3));
    EXPECT_EQ(b.size(), std::size_t{3});
    EXPECT_EQ(contents(b), std::string("a\0b", 3));
}

// ---------------------------------------------------------------------------
// PooledBuffer
// ---------------------------------------------------------------------------

TEST(PooledBuffer, StartsClean) {
    {
        PooledBuffer p;
        EXPECT_TRUE(p->append("first", 5));
    }
    {
        // Must not see the previous call's bytes.
        PooledBuffer p;
        EXPECT_EQ(p->size(), std::size_t{0});
    }
}

TEST(PooledBuffer, ReusesCapacity) {
    std::size_t first_cap = 0;
    {
        PooledBuffer p;
        EXPECT_TRUE(p->append(std::string(4000, 'x').data(), 4000));
        first_cap = p->capacity();
    }
    {
        // This is the property that makes steady-state encoding allocation-free.
        PooledBuffer p;
        EXPECT_EQ(p->capacity(), first_cap);
    }
}

TEST(PooledBuffer, NestingGetsDistinctBuffers) {
    // A default= hook that itself serialises re-enters the encoder, so the pool
    // must hand out a second buffer rather than the one in use.
    PooledBuffer outer;
    EXPECT_TRUE(outer->append("outer", 5));
    {
        PooledBuffer inner;
        EXPECT_TRUE(inner->append("inner", 5));
        EXPECT_EQ(std::string(inner->data(), inner->size()), "inner");
    }
    EXPECT_EQ(std::string(outer->data(), outer->size()), "outer");
}

TEST(PooledBuffer, HugeBuffersAreNotRetained) {
    {
        PooledBuffer p;
        EXPECT_TRUE(p->append(std::string(kMaxPooledCapacity * 2, 'x').data(), kMaxPooledCapacity * 2));
    }
    {
        // Over the cap: released rather than pinned for the process's life.
        PooledBuffer p;
        EXPECT_TRUE(p->capacity() <= kMaxPooledCapacity);
    }
}

TEST(PooledBuffer, PoolIsPerThread) {
    // Thread-local by design: no lock on the hot path, and nothing shared to
    // reason about under a free-threaded build.
    std::vector<std::size_t> sizes(4, 0);
    std::vector<std::thread> threads;
    for (int t = 0; t < 4; ++t) {
        threads.emplace_back([t, &sizes]() {
            for (int i = 0; i < 100; ++i) {
                PooledBuffer p;
                const std::string payload(64 * (t + 1), static_cast<char>('a' + t));
                if (!p->append(payload.data(), payload.size())) return;
                sizes[t] = p->size();
            }
        });
    }
    for (auto& th : threads) th.join();
    for (int t = 0; t < 4; ++t) {
        EXPECT_EQ(sizes[t], static_cast<std::size_t>(64 * (t + 1)));
    }
}

int main() { return ::aqtest::run_all(); }
