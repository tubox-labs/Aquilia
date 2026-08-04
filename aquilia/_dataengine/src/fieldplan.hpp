// fieldplan.hpp -- compiled validation plan (docs/models-engine/05).
//
// Replaces Phase 1+2 of the four-phase seal pipeline -- the per-field body of
// Sigil.validate -- for eligible plans only. @ward methods and the validate()
// hook run afterwards and are untouched.
//
// The target is bottleneck B10: for every field the Python loop re-evaluates
// properties that are fixed at class-build time (isinstance against
// Computed/Constant/Inject, read_only, required, allow_null, default is UNSET).
// Those become flag bits resolved once, and the per-field cast/seal pair
// becomes a switch on a type code with no Python call.
//
// ON ANY FAILURE THE WHOLE PAYLOAD ABORTS to Python. That is deliberate, and it
// differs from what 05 section 3.7 proposed:
//
//   05 suggested caching resolved message strings at compile time. That is not
//   sound -- contract_message() resolves through a request-scoped i18n
//   ContextVar (contracts/messages.py), so the same key yields different text
//   per request locale. Caching at compile time would pin one locale's wording
//   into every later request.
//
//   Aborting instead means failing payloads are re-validated by the identical
//   Python code that handles them today, so messages are byte-identical AND
//   correctly localised for free. The cost falls only on the failure path,
//   which is not the path being optimised.
//
// The same rule covers uncertainty: any input this plan cannot decide with
// certainty defers to Python rather than guessing. A false fallback costs
// speed; a false accept would be a silent correctness bug.
#pragma once

#include <Python.h>

#include <cstdint>
#include <vector>

#include "typecode.hpp"

namespace aq {

// One compiled field. Every member is resolved at plan-build time.
struct FieldOp {
    PyObject* name = nullptr;           // interned field name; strong ref
    PyObject* default_value = nullptr;  // literal only; a callable is ineligible
    // Numeric bounds, compared with PyObject_RichCompare so the semantics are
    // exactly Python's `value < min` / `value > max` for any numeric type.
    PyObject* min_value = nullptr;
    PyObject* max_value = nullptr;
    // Text length bounds in code points, which is what len() counts. -1 = unset.
    Py_ssize_t min_length = -1;
    Py_ssize_t max_length = -1;
    TypeCode code = TypeCode::Unsupported;
    std::uint8_t flags = kFieldNone;
};

class FieldPlan {
public:
    FieldPlan() = default;
    ~FieldPlan();

    // Non-copyable: it owns strong references.
    FieldPlan(const FieldPlan&) = delete;
    FieldPlan& operator=(const FieldPlan&) = delete;

    void add(PyObject* name, TypeCode code, std::uint8_t flags, PyObject* default_value,
             PyObject* min_value, PyObject* max_value, Py_ssize_t min_length, Py_ssize_t max_length);

    // Validate one payload.
    //
    // Returns 1 on success with *validated set to a new dict reference, 0 when
    // the payload must fall back to Python, and -1 on a Python error with the
    // exception set.
    //
    // A 0 return is not an error: the caller re-runs the payload through
    // Sigil.validate, which produces the authoritative (errors, validated).
    int execute(PyObject* payload, PyObject** validated) const;

    std::size_t size() const { return ops_.size(); }

private:
    std::vector<FieldOp> ops_;
};

}  // namespace aq
