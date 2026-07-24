# Performance Improvements

Aquilia 1.3.4 delivers major algorithmic optimizations that drastically reduce CPU utilization and startup times, particularly for large enterprise monorepos.

## O(n²) → O(n) Manifest Registry Lookup

**The Problem:**
In Phase 5 of the framework boot sequence, Aquilia resolves dependencies. Previously, checking if a dependency existed involved iterating over the entire list of manifests: `[m for m in manifests if m.name == target]`. For a project with $N$ apps, where each app depends on $M$ others, this resulted in an $O(N \times M \times N)$ operation—effectively $O(N^2)$ as the project grew.

**The Fix:**
We now pre-build a hash map `{m.name: m}` prior to Phase 5. Manifest lookups are now $O(1)$, bringing the total resolution time down to $O(N)$. 

**Impact:** Large projects (200+ apps) will see startup times drop by several seconds.

## Fast-Path Discovery Cache

**The Problem:**
Aquilia features hot-reloading. To detect changes, the discovery engine calculated a SHA-256 hash for *every* python file in the workspace on every tick. This caused continuous CPU spikes.

**The Fix:**
A fast-path was added to the cache layer. 
1. Check the file size and `mtime` (modification time).
2. If both match the cached state, skip hashing.
3. If either differs, perform the full SHA-256 hash to confirm the content actually changed.

**Impact:** Idle CPU usage during local development is reduced by roughly 85%.

## Iterative Tarjan Algorithm

**The Problem:**
The framework utilizes Tarjan's strongly connected components algorithm to build the dependency graph. The previous implementation used recursion. In Python, recursion is heavily restricted (default limit ~1000 frames). Deep dependency chains (e.g., 500+ modules) would trigger a `RecursionError` and crash the framework.

**The Fix:**
Both the Tarjan algorithm and the `get_transitive_dependencies` helpers were rewritten to use an explicit iterative stack (standard lists in a `while` loop). 

**Impact:** The recursive stack depth is now effectively unlimited, bound only by available memory. 500-module deep architectures now resolve perfectly.
