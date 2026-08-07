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

class FieldPlan;  // self-referential: a nested field owns a sub-plan

// One compiled field. Every member is resolved at plan-build time.
struct FieldOp {
    PyObject* name = nullptr;           // interned field name; strong ref
    PyObject* default_value = nullptr;  // literal only; a callable is ineligible
    // Numeric bounds, compared with PyObject_RichCompare so the semantics are
    // exactly Python's `value < min` / `value > max` for any numeric type.
    PyObject* min_value = nullptr;
    PyObject* max_value = nullptr;
    // IntFacet.multiple_of. Held as an object rather than a C scalar so the
    // modulo runs through PyNumber_Remainder -- Python's % takes the sign of the
    // divisor where C's takes the sign of the dividend, so a C modulo would
    // accept and reject different negative values. FloatFacet.multiple_of uses
    // an epsilon test instead and is escaped at compile time, never seen here.
    PyObject* multiple_of = nullptr;
    // ChoiceFacet: the frozenset of accepted values, built once at compile time.
    // Membership is PySet_Contains, which is the same hash-and-compare the
    // Python `value not in self._valid_values` performs.
    PyObject* choices = nullptr;
    // EnumFacet: the Enum class, plus its two lookup tables captured at compile
    // time. by_value is `_value2member_map_` and by_name is `__members__`; both
    // are read-only mappings the Enum machinery already maintains, so this
    // borrows the existing indexes rather than building a third one.
    PyObject* enum_cls = nullptr;
    PyObject* enum_by_value = nullptr;
    PyObject* enum_by_name = nullptr;
    // Text length bounds in code points, which is what len() counts. -1 = unset.
    Py_ssize_t min_length = -1;
    Py_ssize_t max_length = -1;
    // Container item-count bounds, same -1 = unset convention.
    Py_ssize_t min_items = -1;
    Py_ssize_t max_items = -1;
    // DecimalFacet precision limits, counted from Decimal.as_tuple(). -1 = unset.
    Py_ssize_t max_digits = -1;
    Py_ssize_t decimal_places = -1;
    // TextFacet.pattern: the *compiled* re.Pattern object. Its .search is C code
    // in _sre, so calling it is a builtin call, not user code -- the rule the
    // engine must never break. Reimplementing a regex engine natively would be
    // a second implementation of the most divergence-prone semantics there are.
    PyObject* pattern = nullptr;
    // DictFacet.max_keys, the hash-collision DoS guard. -1 = unset, though the
    // facet defaults it to 1000 so it is effectively always set.
    Py_ssize_t max_keys = -1;
    // NestedContractFacet: the sub-plan for the nested Contract, and a strong
    // reference to the Python object that owns it.
    //
    // Two members for one thing because the raw pointer is what execute()
    // dereferences per payload and the PyObject* is what keeps it alive. The
    // plan is a nanobind-managed object built by the Python compiler, so its
    // lifetime is refcounted like any other; caching the unwrapped pointer
    // avoids a nb::cast per nested field per request.
    PyObject* nested_plan_obj = nullptr;
    const FieldPlan* nested_plan = nullptr;
    TypeCode code = TypeCode::Unsupported;
    // Container shape. When not None, `code` describes the *element* type and
    // the scalar cast is applied per item (per *value*, for Dict).
    ContainerKind container = ContainerKind::None;
    std::uint8_t flags = kFieldNone;
};

// One field as the Python compiler describes it, before the plan takes
// ownership. Mirrors FieldOp, but every PyObject* is BORROWED -- FieldPlan::add
// increfs what it keeps.
//
// Exists so add() has one parameter instead of twenty-two. A positional list
// that long makes every call site a wall of values where inserting one in the
// wrong position is a silent type confusion rather than a compile error.
struct FieldSpec {
    PyObject* name = nullptr;
    TypeCode code = TypeCode::Unsupported;
    ContainerKind container = ContainerKind::None;
    std::uint8_t flags = kFieldNone;
    PyObject* default_value = nullptr;
    PyObject* min_value = nullptr;
    PyObject* max_value = nullptr;
    PyObject* multiple_of = nullptr;
    PyObject* choices = nullptr;
    PyObject* enum_cls = nullptr;
    PyObject* enum_by_value = nullptr;
    PyObject* enum_by_name = nullptr;
    PyObject* pattern = nullptr;
    PyObject* nested_plan_obj = nullptr;
    const FieldPlan* nested_plan = nullptr;
    Py_ssize_t min_length = -1;
    Py_ssize_t max_length = -1;
    Py_ssize_t min_items = -1;
    Py_ssize_t max_items = -1;
    Py_ssize_t max_digits = -1;
    Py_ssize_t decimal_places = -1;
    Py_ssize_t max_keys = -1;
};

class FieldPlan {
public:
    FieldPlan() = default;
    ~FieldPlan();

    // Non-copyable: it owns strong references.
    FieldPlan(const FieldPlan&) = delete;
    FieldPlan& operator=(const FieldPlan&) = delete;

    // Append one compiled field.
    //
    // Takes a spec struct rather than a positional argument list: the list had
    // reached eighteen parameters, where every call site is a wall of
    // positional values and inserting one in the wrong place is a silent
    // type-confusion bug rather than a compile error.
    //
    // Every PyObject* in the spec is BORROWED; add() takes its own strong
    // references and the plan releases them in its destructor.
    void add(const FieldSpec& spec);

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
