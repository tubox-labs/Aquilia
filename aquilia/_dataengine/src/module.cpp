// module.cpp -- nanobind glue for aquilia._dataengine.
//
// The only translation unit in this extension that is Python-aware, mirroring
// the split in aquilia/_core. Everything else is plain C++ so it can be unit
// tested and sanitized without an interpreter in the process.
//
// This engine is the data path: hydration (RowPlan) and validation (FieldPlan).
// It is deliberately separate from _core, which is the request path -- see
// docs/models-engine/03-engine-design.md section 3. An app that touches neither
// the ORM nor contracts pays nothing for this code, and either extension can be
// disabled without affecting the other.

#include <nanobind/nanobind.h>

namespace nb = nanobind;

NB_MODULE(_dataengine, m) {
    m.doc() = "Aquilia native data engine: batch hydration and validation plans.";

    // Boundary-cost probe. benchmarks/models/boundary.py measures the crossing
    // against this, and the whole batch-vs-per-field design rests on that
    // number, so it ships rather than living in a scratch file.
    m.def("noop", []() {}, "Do nothing. Used to measure the Python<->native call cost.");
}
