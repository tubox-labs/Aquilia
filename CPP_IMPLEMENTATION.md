Aquilia Core Engine — Architecture & Implementation Agent (Phase 1)

Objective

Create a new branch for this task 

Your mission is NOT to immediately write code.

Your first responsibility is to become an expert on the Aquilia architecture.

Before modifying a single line of code, you must completely understand the existing architecture, design philosophy, lifecycle, dependency graph, extension points, conventions, and internal execution flow.

Do not begin implementation until the analysis phase has been completed and validated.

The implementation must preserve Aquilia's public developer experience while replacing performance-critical internals with a production-grade native C++ engine exposed through Python bindings.

Critical Rule

Do not make changes during the analysis phase.

No code generation.

No refactoring.

No architecture changes.

No assumptions.

No shortcuts.

No "best guess."

Your understanding must be based entirely on the existing codebase.

---

Phase 1 — Complete Codebase Analysis

Read and analyse the entire Aquilia repository, including every package, subsystem, internal utility, and execution path.

Build a complete mental model of the framework.

The analysis must include (but is not limited to):

- Complete request lifecycle
- Complete application lifecycle
- ASGI flow
- Server startup
- Shutdown sequence
- Engine architecture
- Module system
- Dependency Injection
- Router
- Middleware
- Manifest system
- Workspace
- Configuration
- Context management
- Request/Response pipeline
- Reflection system
- Decorators
- Metadata generation
- Validation
- Serialization
- Utilities
- Internal caches
- Object lifecycle
- Plugin system
- CLI interactions
- Extension APIs
- Thread safety
- Async execution
- Import graph
- Circular dependency analysis
- Package boundaries
- Internal architecture patterns

Understand:

- why it was implemented this way
- where performance bottlenecks exist
- where unnecessary allocations occur
- where reflection is repeatedly performed
- where metadata is rebuilt
- where Python overhead dominates execution

Produce dependency graphs and execution flow diagrams before implementation.

---

Phase 2 — Performance Audit

Perform a production-grade performance audit.

Identify:

- Hot paths
- Cold paths
- CPU intensive operations
- Memory intensive operations
- Repeated reflection
- Repeated imports
- Repeated object creation
- Dynamic dispatch
- Dictionary lookups
- Metadata generation
- Dataclass overhead
- DI overhead
- Router lookup complexity
- Allocation hotspots
- Lock contention
- Async bottlenecks
- Cache misses

Every identified bottleneck must include:

- Root cause
- Current implementation
- Performance impact
- Proposed native replacement
- Estimated complexity
- Estimated performance gain
- Tradeoffs
- Risks

Do not rely on assumptions.

Support every recommendation with evidence from the codebase.

---

Phase 3 — Design the Aquilia Core Engine

Do NOT think of this as "rewriting DI in C++."

Instead design a reusable, extensible, high-performance Aquilia Core Engine that becomes the runtime foundation for every future native subsystem.

The engine must not be hard-coded to DI or routing.

Instead it must expose reusable primitives that any Aquilia subsystem can build upon.

Future subsystems should be implementable almost entirely using this engine.

Examples include:

- Routing
- Dependency Injection
- Validation
- Serialization
- Middleware
- Lifecycle
- Request objects
- Response objects
- Template runtime
- ORM internals
- Metadata
- Reflection
- Configuration
- Caching
- Future plugins

Design for long-term extensibility rather than immediate implementation.

---

Engine Design Requirements

The engine architecture must include:

- Runtime architecture
- Layered architecture
- Internal module boundaries
- Public API
- Internal API
- Stable ABI strategy
- Python binding strategy
- Memory model
- Ownership model
- Thread safety
- Async compatibility
- Object model
- Reflection model
- Metadata registry
- Type registry
- Internal caches
- String interning
- Arena allocators
- Object pools
- Memory pools
- Lock-free structures where appropriate
- Error propagation
- Diagnostics
- Logging hooks
- Instrumentation
- Profiling hooks
- Debug mode
- Release mode
- Feature flags
- Compile-time configuration
- Runtime configuration
- Benchmarking interfaces

The architecture should resemble an industry-grade runtime rather than a collection of native helper modules.

---

Python Integration

The Python API must remain the primary developer interface.

Users should continue writing normal Aquilia applications.

Example:

- decorators
- modules
- controllers
- services
- manifests
- configuration

must remain Python-first.

The Python layer should translate high-level constructs into engine operations.

The C++ engine should execute the heavy computation.

Never expose unnecessary C++ complexity to framework users.

---

Phase 4 — Design the Native DI Engine

Design a production-grade Dependency Injection engine using the Core Engine primitives.

Do not immediately implement.

First produce a full architecture specification.

Include:

- Service registry
- Provider registry
- Dependency graph
- Graph compilation
- Constructor injection
- Property injection (if supported)
- Factory providers
- Async providers
- Singleton scope
- Scoped services
- Transient services
- Lazy services
- Circular dependency detection
- Graph validation
- Graph optimisation
- Resolution caching
- Thread safety
- Async compatibility
- Error reporting
- Diagnostics
- Profiling
- Metadata integration
- Reflection integration

Explain why each architectural decision was made.

---

Phase 5 — Design the Native Routing Engine

Design a production-grade routing engine.

The router must support future framework evolution.

Include:

- Route registration
- Route compilation
- Static routes
- Dynamic routes
- Parameter extraction
- Typed parameters
- Regex routes
- Wildcards
- HTTP methods
- Trie / Radix tree comparison
- Route optimisation
- Route cache
- Route metadata
- Reverse routing
- Middleware integration
- Route groups
- Nested routers
- Prefix optimisation
- Matching algorithm analysis
- Complexity analysis

Benchmark multiple routing algorithms before selecting one.

Justify every decision.

---

Phase 6 — Python Binding Architecture

Design the binding layer.

Include:

- nanobind architecture
- Module organisation
- Lifetime management
- Exception translation
- Zero-copy opportunities
- Ownership semantics
- GIL management
- ABI compatibility
- Wheel compatibility
- Packaging strategy
- Build system
- CI/CD wheel generation
- Cross-platform support

The binding layer should remain thin.

The engine should own the business logic.

---

Phase 7 — Testing Strategy

Design a complete testing architecture before implementation.

Include:

- Unit tests
- Integration tests
- Functional tests
- API compatibility tests
- Regression tests
- Property-based tests
- Fuzz testing
- Concurrency testing
- Memory correctness tests
- Thread safety validation
- Stress testing
- Long-running soak tests
- Performance regression tests
- ABI compatibility tests
- Python compatibility tests

Target near-complete coverage of new native code.

---

Phase 8 — Benchmark Suite

Create an industry-grade benchmark suite.

Benchmark against the current Aquilia implementation.

Measure:

- Route registration
- Route lookup
- Parameter extraction
- DI graph construction
- DI resolution
- Cold start
- Warm start
- Request throughput
- P50 latency
- P95 latency 
- P99 latency
- Allocation count
- CPU usage
- Memory usage
- Startup time
- Cache hit rates

Run benchmarks under varying loads (single-threaded, highly concurrent, and sustained stress) and document methodology to ensure reproducibility.

---

Phase 9 — Implementation Standards

Every implementation must adhere to production-quality standards.

Requirements:

- Modern C++ (C++20 or newer where appropriate)
- Fully typed interfaces
- Strong ownership semantics
- RAII
- Exception-safe code
- Comprehensive documentation
- Doxygen-compatible comments where applicable
- Consistent naming conventions
- SOLID principles where appropriate
- Composition over inheritance
- Minimal runtime allocations
- Cache-friendly data structures
- Profiling-friendly design
- Zero undefined behaviour
- High maintainability
- Clear separation of public and internal APIs

The Python layer must also include:

- Complete type hints
- Rich docstrings
- Developer documentation
- API reference updates
- Usage examples

---

Deliverables (Before Any Implementation)

Before writing production code, produce:

1. Complete architectural audit of the existing Aquilia codebase.
2. Performance bottleneck report with evidence.
3. Comprehensive Aquilia Core Engine architecture document.
4. Native Dependency Injection architecture specification.
5. Native Routing architecture specification.
6. Python binding architecture.
7. Testing strategy.
8. Benchmarking strategy.
9. Migration strategy from the existing Python implementation.
10. Risk assessment and mitigation plan.
11. Implementation roadmap broken into incremental milestones with clear acceptance criteria.

Only after these documents are reviewed and internally validated should implementation begin. Every implementation decision must be traceable back to the analysis and architecture documents rather than assumptions.