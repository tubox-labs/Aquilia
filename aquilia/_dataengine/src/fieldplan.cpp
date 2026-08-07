#include "fieldplan.hpp"

#include <cassert>
#include <cmath>

#include "convert.hpp"

namespace aq {
namespace {

// Outcome of one field's cast. kFallback means "this plan cannot decide with
// certainty" -- the caller re-runs the whole payload in Python rather than
// guessing, which is what keeps the two paths from diverging.
enum class Step { kOk, kFallback, kError };

// ASCII whitespace, matching what TextFacet's str.strip() would remove from an
// ASCII string. Non-ASCII strings are never inspected here (see cast_text).
inline bool is_ascii_space(Py_UCS4 c) {
    return c == ' ' || c == '\t' || c == '\n' || c == '\r' || c == '\v' || c == '\f';
}

// IntFacet.cast semantics, reproduced exactly (facets.py:1449, pinned row by row
// in 05 section 3.1). These are deliberate, counter-intuitive decisions and are
// precisely where a naive strtoll-style reimplementation would silently diverge:
//
//   True/False   rejected -- bool is an int subclass, so accepting it would let
//                True become 1
//   3.0          accepted -- no information is lost
//   3.9          REJECTED, not truncated. Truncation is silent data corruption:
//                a client sending {"quantity": 3.9} would get 3 persisted with
//                no indication anything was dropped.
//   NaN, +-inf   rejected
//   Decimal      same integral-value rule as float; deferred to Python here
//
// Every rejection returns kFallback so Python raises the real CastFault.
Step cast_int(PyObject* raw, PyObject** out) {
    // Checked before PyLong, because bool IS a PyLong subclass.
    if (PyBool_Check(raw)) return Step::kFallback;

    if (PyLong_CheckExact(raw)) {
        *out = Py_NewRef(raw);
        return Step::kOk;
    }

    if (PyFloat_CheckExact(raw)) {
        const double d = PyFloat_AS_DOUBLE(raw);
        // NaN fails self-comparison.
        if (d != d || std::isinf(d)) return Step::kFallback;
        double integral = 0.0;
        if (std::modf(d, &integral) != 0.0) return Step::kFallback;  // 3.9 -> reject
        PyObject* v = PyLong_FromDouble(d);
        if (!v) return Step::kError;
        *out = v;
        return Step::kOk;
    }

    if (PyUnicode_CheckExact(raw)) {
        // int(str) -- CPython's own parser, which rejects "3.9" for us.
        PyObject* v = PyNumber_Long(raw);
        if (!v) {
            PyErr_Clear();  // Python will raise the real CastFault
            return Step::kFallback;
        }
        *out = v;
        return Step::kOk;
    }

    // Decimal and everything else: let Python decide.
    return Step::kFallback;
}

// TextFacet.cast + the blank check from seal.
//
// trim defaults to True, so ignoring it would diverge on almost every contract.
// Rather than reimplement str.strip()'s Unicode whitespace rules, this only
// handles ASCII strings that need no trimming at all -- the overwhelmingly
// common case -- and defers everything else.
Step cast_text(PyObject* raw, std::uint8_t flags, PyObject** out) {
    if (!PyUnicode_CheckExact(raw)) {
        // int/float/bool coerce to str in Python; rarer, so defer.
        return Step::kFallback;
    }

    const Py_ssize_t len = PyUnicode_GET_LENGTH(raw);

    if (flags & kFieldTrim) {
        // Only ASCII can be checked cheaply and exactly against str.strip().
        if (!PyUnicode_IS_ASCII(raw)) return Step::kFallback;
        if (len > 0) {
            const Py_UCS4 first = PyUnicode_READ_CHAR(raw, 0);
            const Py_UCS4 last = PyUnicode_READ_CHAR(raw, len - 1);
            // Would strip: hand it to Python, which owns the trim.
            if (is_ascii_space(first) || is_ascii_space(last)) return Step::kFallback;
        }
    }

    // TextFacet.seal rejects "" unless allow_blank.
    if (len == 0 && !(flags & kFieldAllowBlank)) return Step::kFallback;

    *out = Py_NewRef(raw);
    return Step::kOk;
}

// FloatFacet.cast. allow_nan/allow_infinity default to False, so any non-finite
// result defers rather than encoding both flags.
Step cast_float(PyObject* raw, PyObject** out) {
    if (PyBool_Check(raw)) return Step::kFallback;

    if (PyFloat_CheckExact(raw)) {
        const double d = PyFloat_AS_DOUBLE(raw);
        if (d != d || std::isinf(d)) return Step::kFallback;
        *out = Py_NewRef(raw);
        return Step::kOk;
    }
    if (PyLong_CheckExact(raw) || PyUnicode_CheckExact(raw)) {
        PyObject* v = PyNumber_Float(raw);
        if (!v) {
            PyErr_Clear();
            return Step::kFallback;
        }
        const double d = PyFloat_AS_DOUBLE(v);
        if (d != d || std::isinf(d)) {
            Py_DECREF(v);
            return Step::kFallback;
        }
        *out = v;
        return Step::kOk;
    }
    return Step::kFallback;
}

Step cast_bool(PyObject* raw, PyObject** out) {
    if (PyBool_Check(raw)) {
        *out = Py_NewRef(raw);
        return Step::kOk;
    }
    // BoolFacet accepts a documented token set ("true"/"1"/"yes"/...). Encoding
    // it here would duplicate a table that lives in Python; defer.
    return Step::kFallback;
}

// Date/DateTime/Time from an ISO-8601 string, which is how they arrive in a JSON
// payload -- the common case, so it is worth handling rather than deferring.
//
// Safe because each facet's cast() is exactly `X.fromisoformat(value)` for a str
// input (facets.py), and fromisoformat is C in CPython at 18-25 ns -- cheaper
// than reimplementing ISO-8601 and risking timezone or fractional-second
// divergence. A ValueError means the same CastFault Python would raise, so it
// defers rather than reporting the error itself.
Step cast_iso(PyObject* raw, PyTypeObject* want, PyObject* fromisoformat, PyObject** out) {
    if (Py_IS_TYPE(raw, want)) {
        *out = Py_NewRef(raw);
        return Step::kOk;
    }
    if (!PyUnicode_CheckExact(raw)) return Step::kFallback;
    PyObject* v = PyObject_CallFunctionObjArgs(fromisoformat, raw, nullptr);
    if (!v) {
        PyErr_Clear();
        return Step::kFallback;
    }
    // Confirm the exact type rather than trusting the constructor, so a
    // subclass instance can never reach a facet expecting the base type.
    if (!Py_IS_TYPE(v, want)) {
        Py_DECREF(v);
        return Step::kFallback;
    }
    *out = v;
    return Step::kOk;
}

Step cast_uuid(PyObject* raw, PyObject** out) {
    if (Py_IS_TYPE(raw, ctors().uuid_type)) {
        *out = Py_NewRef(raw);
        return Step::kOk;
    }
    if (!PyUnicode_CheckExact(raw)) return Step::kFallback;
    PyObject* u = uuid_from_string(raw);
    if (u) {
        *out = u;
        return Step::kOk;
    }
    if (PyErr_Occurred()) PyErr_Clear();
    return Step::kFallback;
}

// EnumFacet.cast (facets.py:2916), reproduced for the cases that are decidable
// without running Python code.
//
// The Python order is load-bearing and reproduced exactly:
//   1. isinstance(value, enum_class)  -> return as-is
//   2. numeric/string coercion for IntEnum/StrEnum subclasses
//   3. enum_class(coerced)            -> lookup BY VALUE
//   4. value in __members__           -> lookup BY NAME
//   5. raise CastFault
//
// Step 3 is `enum_class(value)`, which invokes EnumMeta.__call__ and can run a
// user-defined `_missing_` hook. That hook is arbitrary Python, so a class that
// defines one is escaped at compile time and never reaches here -- leaving
// `_value2member_map_`, the plain index EnumMeta consults first, as an exact
// stand-in for the call.
//
// The IntEnum/StrEnum coercion in step 2 is deliberately NOT reproduced: it
// calls int(value)/str(value) on arbitrary input and then retries the lookup.
// A miss here therefore defers rather than rejecting, so Python still gets to
// try the coercion path.
Step cast_enum(PyObject* raw, const FieldOp& op, PyObject** out) {
    // Step 1: already a member of this Enum.
    const int is_member = PyObject_IsInstance(raw, op.enum_cls);
    if (is_member < 0) return Step::kError;
    if (is_member) {
        *out = Py_NewRef(raw);
        return Step::kOk;
    }

    // Step 3: by value. PyDict_GetItemWithError on an unhashable key sets
    // TypeError, which is cleared -- Python's own lookup would raise the same
    // and report it as this field's error.
    PyObject* member = PyDict_GetItemWithError(op.enum_by_value, raw);
    if (member) {
        *out = Py_NewRef(member);
        return Step::kOk;
    }
    if (PyErr_Occurred()) {
        PyErr_Clear();
        return Step::kFallback;
    }

    // Step 4: by name, str keys only -- __members__ is keyed by identifier.
    if (PyUnicode_CheckExact(raw)) {
        member = PyDict_GetItemWithError(op.enum_by_name, raw);
        if (member) {
            *out = Py_NewRef(member);
            return Step::kOk;
        }
        if (PyErr_Occurred()) {
            PyErr_Clear();
            return Step::kFallback;
        }
    }

    // Miss. Python may still coerce (IntEnum/StrEnum) or raise; either way it
    // owns the outcome.
    return Step::kFallback;
}

// DurationFacet.cast (facets.py:2016) for the two shapes that are exact.
//
//   timedelta   -> returned as-is
//   int/float   -> timedelta(seconds=value)
//   str         -> deferred: the Python branch tries float(), then splits on
//                  ":" for HH:MM:SS, and reproducing both plus their sign
//                  handling natively buys nothing over the C constructor.
//
// bool is rejected before the numeric branch. `isinstance(True, int)` is true in
// Python, so DurationFacet actually accepts True and yields timedelta(seconds=1)
// -- but that is surprising enough that reproducing it natively is not worth the
// risk of getting it subtly wrong; deferring lets Python do exactly what it does.
Step cast_duration(PyObject* raw, PyObject** out) {
    if (Py_IS_TYPE(raw, ctors().timedelta_type)) {
        *out = Py_NewRef(raw);
        return Step::kOk;
    }
    if (PyBool_Check(raw)) return Step::kFallback;
    if (!PyLong_CheckExact(raw) && !PyFloat_CheckExact(raw)) return Step::kFallback;

    // A float that is NaN or infinite makes timedelta raise; let Python report it.
    if (PyFloat_CheckExact(raw)) {
        const double d = PyFloat_AS_DOUBLE(raw);
        if (d != d || std::isinf(d)) return Step::kFallback;
    }

    // timedelta(seconds=value) -- the keyword matters, a positional argument
    // would mean days.
    PyObject* kwargs = PyDict_New();
    if (!kwargs) return Step::kError;
    if (PyDict_SetItemString(kwargs, "seconds", raw) < 0) {
        Py_DECREF(kwargs);
        return Step::kError;
    }
    PyObject* empty = PyTuple_New(0);
    if (!empty) {
        Py_DECREF(kwargs);
        return Step::kError;
    }
    PyObject* v = PyObject_Call(reinterpret_cast<PyObject*>(ctors().timedelta_type), empty, kwargs);
    Py_DECREF(empty);
    Py_DECREF(kwargs);
    if (!v) {
        // OverflowError for an out-of-range value; Python raises the same.
        PyErr_Clear();
        return Step::kFallback;
    }
    *out = v;
    return Step::kOk;
}

// DecimalFacet.cast (facets.py:1667): Decimal(str(value)).
//
// The str() is load-bearing for float input -- Decimal(0.1) keeps the binary
// representation error (0.1000000000000000055511151231257827) while
// Decimal(str(0.1)) is exactly Decimal("0.1"). Python applies it to floats only;
// this handles str and int input (where str() is either a no-op or exact) and
// defers floats so the conversion Python performs is the one that happens.
Step cast_decimal(PyObject* raw, PyObject** out) {
    if (Py_IS_TYPE(raw, reinterpret_cast<PyTypeObject*>(ctors().decimal_type))) {
        *out = Py_NewRef(raw);
        return Step::kOk;
    }
    // bool is an int subclass; Decimal(True) is Decimal(1), which is legal but
    // surprising enough to defer.
    if (PyBool_Check(raw)) return Step::kFallback;
    if (!PyUnicode_CheckExact(raw) && !PyLong_CheckExact(raw)) return Step::kFallback;

    PyObject* v = PyObject_CallFunctionObjArgs(ctors().decimal_type, raw, nullptr);
    if (!v) {
        PyErr_Clear();  // InvalidOperation -- Python raises the real CastFault
        return Step::kFallback;
    }
    // NaN and Infinity parse successfully but compare unusably against bounds,
    // and DecimalFacet.seal has no guard for them. Defer so behaviour matches
    // whatever Python does rather than whatever this code would do.
    PyObject* finite = PyObject_CallMethod(v, "is_finite", nullptr);
    if (!finite) {
        Py_DECREF(v);
        return Step::kError;
    }
    const int ok = PyObject_IsTrue(finite);
    Py_DECREF(finite);
    if (ok < 0) {
        Py_DECREF(v);
        return Step::kError;
    }
    if (!ok) {
        Py_DECREF(v);
        return Step::kFallback;
    }
    *out = v;
    return Step::kOk;
}

// DecimalFacet.seal precision limits (facets.py:1680).
//
// Both are read off Decimal.as_tuple(), exactly as Python does:
//   max_digits      len(digits)                 -- total significant digits
//   decimal_places  -exponent if exponent < 0   -- fractional digits
//
// Note this counts *significant* digits, so Decimal("0.001") has one digit and
// three places. That is what the Python code counts too, surprising as it is.
Step check_decimal_precision(const FieldOp& op, PyObject* value) {
    if (op.max_digits < 0 && op.decimal_places < 0) return Step::kOk;

    PyObject* tuple = PyObject_CallMethod(value, "as_tuple", nullptr);
    if (!tuple) return Step::kError;
    if (!PyTuple_Check(tuple) || PyTuple_GET_SIZE(tuple) != 3) {
        Py_DECREF(tuple);
        return Step::kFallback;
    }

    PyObject* digits = PyTuple_GET_ITEM(tuple, 1);   // borrowed
    PyObject* exponent = PyTuple_GET_ITEM(tuple, 2);  // borrowed

    Step result = Step::kOk;

    if (op.max_digits >= 0) {
        if (!PyTuple_Check(digits)) {
            Py_DECREF(tuple);
            return Step::kFallback;
        }
        if (PyTuple_GET_SIZE(digits) > op.max_digits) result = Step::kFallback;
    }

    if (result == Step::kOk && op.decimal_places >= 0) {
        // A non-finite Decimal has a string exponent ("n", "N", "F"); those are
        // rejected during cast, so this is an int here. Checked anyway rather
        // than assumed, since a wrong branch would silently accept.
        if (!PyLong_CheckExact(exponent)) {
            Py_DECREF(tuple);
            return Step::kFallback;
        }
        const long exp = PyLong_AsLong(exponent);
        if (exp == -1 && PyErr_Occurred()) {
            PyErr_Clear();
            Py_DECREF(tuple);
            return Step::kFallback;
        }
        const long places = exp < 0 ? -exp : 0;
        if (places > op.decimal_places) result = Step::kFallback;
    }

    Py_DECREF(tuple);
    return result;
}


// ChoiceFacet / LiteralFacet.
//
// ChoiceFacet.cast is the identity (facets.py) -- it performs no coercion at
// all, so "1" and 1 are distinct choices. Reproducing that is trivial and the
// whole value of the code is in seal: `value not in self._valid_values`.
//
// PySet_Contains is exactly that operator -- same hash, same __eq__ -- so a
// choice set of ints, strings, enum members, or a mix behaves identically. A
// value that is unhashable raises TypeError inside PySet_Contains, which is what
// Python's `in` would raise too; it is cleared and deferred so the Python path
// produces the real CastFault rather than propagating a bare TypeError.
//
// LiteralFacet is a ChoiceFacet whose set holds exactly one value (it calls
// super().__init__(choices=[value])), so it needs no separate implementation --
// the compiler emits the same one-element frozenset and this same code runs.
Step seal_choice(const FieldOp& op, PyObject* value) {
    const int contained = PySet_Contains(op.choices, value);
    if (contained < 0) {
        // Unhashable value. Python's `in` raises here too, and Sigil.validate
        // catches it as the field's error message.
        PyErr_Clear();
        return Step::kFallback;
    }
    return contained ? Step::kOk : Step::kFallback;
}

// IntFacet.seal / FloatFacet.seal multiple_of.
//
// The two facets use *different* tests and this reproduces only the integer
// one, which is exact:
//
//   IntFacet:   value % multiple_of != 0                      -- exact
//   FloatFacet: abs(v/m - round(v/m)) > 1e-9                  -- epsilon
//
// The float test is deliberately NOT reproduced here. Its result depends on
// binary rounding at the epsilon boundary, and matching it bit-for-bit across
// platforms is not something this code can promise, so a FloatFacet carrying
// multiple_of is escaped by the compiler and never reaches this function.
//
// PyNumber_Remainder rather than a C modulo: Python's % on negative operands
// takes the sign of the divisor (-7 % 5 == 3), where C's takes the sign of the
// dividend (-7 % 5 == -2). A C modulo would therefore accept and reject
// different negative values than facets.py does.
Step check_multiple_of(const FieldOp& op, PyObject* value) {
    if (!op.multiple_of) return Step::kOk;

    PyObject* remainder = PyNumber_Remainder(value, op.multiple_of);
    if (!remainder) {
        // ZeroDivisionError, or a type pairing that has no %. Python raises the
        // same thing and reports it as the field's error.
        PyErr_Clear();
        return Step::kFallback;
    }

    const int nonzero = PyObject_IsTrue(remainder);
    Py_DECREF(remainder);
    if (nonzero < 0) return Step::kError;
    // `!= 0` in Python; a non-zero remainder fails the constraint.
    return nonzero ? Step::kFallback : Step::kOk;
}

// Container item-count bounds (ListFacet/SetFacet/TupleFacet.seal).
//
// Applied in the same order as facets.py: min_items first, then max_items, so
// the message Python goes on to render describes the same violation. PyObject_Size
// rather than a per-type macro, because the value here is already the *converted*
// container -- a set for SetFacet, a tuple for TupleFacet -- and the count is
// taken after conversion, which is what Python does. That matters for SetFacet:
// duplicates are gone by this point, so [1,1,1] with min_items=2 fails.
Step check_item_counts(const FieldOp& op, PyObject* value) {
    if (op.min_items < 0 && op.max_items < 0) return Step::kOk;
    const Py_ssize_t len = PyObject_Size(value);
    if (len < 0) {
        PyErr_Clear();
        return Step::kFallback;
    }
    if (op.min_items >= 0 && len < op.min_items) return Step::kFallback;
    if (op.max_items >= 0 && len > op.max_items) return Step::kFallback;
    return Step::kOk;
}

// Bounds, in the order IntFacet.seal applies them: min then max. The first
// violation is what Python reports, so order is observable.
// Returns kOk when the value passes, kFallback when it does not (Python raises
// the real error with the localised message).
Step check_bounds(const FieldOp& op, PyObject* value) {
    if (op.min_value) {
        const int lt = PyObject_RichCompareBool(value, op.min_value, Py_LT);
        if (lt < 0) return Step::kError;
        if (lt) return Step::kFallback;
    }
    if (op.max_value) {
        const int gt = PyObject_RichCompareBool(value, op.max_value, Py_GT);
        if (gt < 0) return Step::kError;
        if (gt) return Step::kFallback;
    }
    return Step::kOk;
}

Step check_lengths(const FieldOp& op, PyObject* value) {
    if (op.min_length < 0 && op.max_length < 0) return Step::kOk;
    // Only str reaches here; PyUnicode_GET_LENGTH counts code points, which is
    // exactly what len() returns.
    const Py_ssize_t len = PyUnicode_GET_LENGTH(value);
    if (op.min_length >= 0 && len < op.min_length) return Step::kFallback;
    if (op.max_length >= 0 && len > op.max_length) return Step::kFallback;
    return Step::kOk;
}

// TextFacet.seal pattern check (facets.py:796): `self.pattern.search(value)`.
//
// The compiled re.Pattern is called rather than reimplemented. Its .search is C
// code in _sre, so this is a builtin call, not user Python -- the rule the
// engine must never break. Writing a regex engine natively would be a second
// implementation of the single most divergence-prone semantics in the codebase,
// for a matcher CPython already provides in C.
//
// Note it is search(), not match() or fullmatch(): an unanchored pattern matches
// anywhere in the string, which is a real behavioural quirk of TextFacet and is
// preserved exactly by calling the same method.
Step check_pattern(const FieldOp& op, PyObject* value) {
    if (!op.pattern) return Step::kOk;

    PyObject* result = PyObject_CallMethodOneArg(op.pattern, ctors().str_search, value);
    if (!result) {
        // A pattern object that does not behave like re.Pattern. Python raises
        // the same thing and reports it as this field's error.
        PyErr_Clear();
        return Step::kFallback;
    }
    // re.search returns None on no match, a Match object otherwise.
    const bool matched = result != Py_None;
    Py_DECREF(result);
    return matched ? Step::kOk : Step::kFallback;
}

// BytesFacet.cast (facets.py:1327) for the shapes that are exact.
//
//   bytes                -> returned as-is
//   bytearray/memoryview -> bytes(value)
//   str                  -> deferred
//
// The str branch decodes base64 or hex, and base64.b64decode(validate=True) has
// specific padding and alphabet rules that are not worth reproducing when the
// stdlib already implements them in C. Deferring costs one Python pass on a
// field type that is rare in hot paths.
Step cast_bytes(PyObject* raw, PyObject** out) {
    if (PyBytes_CheckExact(raw)) {
        *out = Py_NewRef(raw);
        return Step::kOk;
    }
    if (PyByteArray_CheckExact(raw)) {
        // PyBytes_FromObject rather than PyByteArray_AS_STRING: that macro
        // references _PyByteArray_empty_string, which is not exported by every
        // CPython build (this one included), and an extension that fails to
        // link on some interpreters is worse than one function call.
        PyObject* v = PyBytes_FromObject(raw);
        if (!v) {
            PyErr_Clear();
            return Step::kFallback;
        }
        *out = v;
        return Step::kOk;
    }
    return Step::kFallback;
}

// BytesFacet.seal size bounds (facets.py:1353). Counts *decoded* bytes, which
// is what len() on the cast value returns.
Step check_byte_lengths(const FieldOp& op, PyObject* value) {
    if (op.min_length < 0 && op.max_length < 0) return Step::kOk;
    const Py_ssize_t len = PyBytes_GET_SIZE(value);
    if (op.min_length >= 0 && len < op.min_length) return Step::kFallback;
    if (op.max_length >= 0 && len > op.max_length) return Step::kFallback;
    return Step::kOk;
}

// A single nested Contract: run its sub-plan over the payload.
//
// Only an exact dict qualifies. Sigil.validate runs adapt_input() first, which
// converts dataclass and attrs instances to mappings; those shapes are not
// modelled here and defer.
//
// A sub-plan that itself declines (rc == 0) propagates as kFallback, so the
// WHOLE outer payload re-runs in Python. That is deliberate and matches the
// existing contract: the outer plan cannot emit a partial result, and the
// nested Contract's own error paths -- including its ward methods and its
// message localisation -- belong to Python.
Step cast_nested(PyObject* raw, const FieldOp& op, PyObject** out) {
    if (!PyDict_CheckExact(raw)) return Step::kFallback;
    PyObject* sub = nullptr;
    const int rc = op.nested_plan->execute(raw, &sub);
    if (rc < 0) return Step::kError;
    if (rc == 0) return Step::kFallback;
    *out = sub;
    return Step::kOk;
}

// One element of a container, cast by the same function the scalar path uses.
//
// Sharing the scalar casts is the whole point: there is no second implementation
// of a type's semantics that could drift from the first. Element casts are
// called with kFieldNone rather than the field's flags, because trim/allow_blank
// belong to the container facet itself and are not propagated to its child (the
// compiler escapes any child that carries constraints of its own).
//
// Takes the whole op rather than just a TypeCode so a nested Contract composes
// with every container -- `list[ItemContract]` is one sub-plan applied per item.
Step cast_element(PyObject* item, const FieldOp& op, PyObject** out) {
    switch (op.code) {
        case TypeCode::Passthrough:
            // DictFacet with no value_facet: Python stores `result[k] = v`
            // untouched, so anything at all is accepted here.
            *out = Py_NewRef(item);
            return Step::kOk;
        case TypeCode::Str:
            return cast_text(item, kFieldNone, out);
        case TypeCode::Int:
            return cast_int(item, out);
        case TypeCode::Float:
            return cast_float(item, out);
        case TypeCode::Bool:
            return cast_bool(item, out);
        case TypeCode::Uuid:
            return cast_uuid(item, out);
        case TypeCode::Date:
            return cast_iso(item, ctors().date_type, ctors().date_fromisoformat, out);
        case TypeCode::DateTime:
            return cast_iso(item, ctors().datetime_type, ctors().datetime_fromisoformat, out);
        case TypeCode::Time:
            return cast_iso(item, ctors().time_type, ctors().time_fromisoformat, out);
        case TypeCode::Nested: {
            // Each element is a whole nested payload validated by its own plan.
            // Only an exact dict qualifies: Sigil runs adapt_input() first, and
            // the shapes it adapts (dataclass, attrs) are not modelled here.
            if (!PyDict_CheckExact(item)) return Step::kFallback;
            PyObject* sub = nullptr;
            const int rc = op.nested_plan->execute(item, &sub);
            if (rc < 0) return Step::kError;
            if (rc == 0) return Step::kFallback;
            *out = sub;
            return Step::kOk;
        }
        default:
            return Step::kFallback;
    }
}

// DictFacet.cast (facets.py:2508).
//
// Reproduced: the dict type check, the max_keys DoS guard, the string-key
// requirement, and the per-value cast. Deliberately NOT reproduced: the
// JSON-string branch, where a str that looks like `{...}` is json.loads'd first.
// That branch is escaped by the compiler being handed only dict input here --
// a str defers, and Python parses it.
//
// Python builds a NEW dict in cast and, when a value_facet is present, another
// in seal. The value stored is therefore always a fresh dict, never the caller's
// -- reproduced here so a caller mutating the payload afterwards cannot be
// observed differently between the two paths.
Step cast_dict(PyObject* raw, const FieldOp& op, PyObject** out) {
    if (!PyDict_CheckExact(raw)) return Step::kFallback;

    const Py_ssize_t size = PyDict_GET_SIZE(raw);
    if (op.max_keys >= 0 && size > op.max_keys) return Step::kFallback;

    PyObject* result = PyDict_New();
    if (!result) return Step::kError;

    PyObject* key = nullptr;
    PyObject* value = nullptr;
    Py_ssize_t pos = 0;
    while (PyDict_Next(raw, &pos, &key, &value)) {
        // Both borrowed; `raw` owns them and is not mutated during the walk.
        if (!PyUnicode_CheckExact(key)) {
            // Python raises "Dictionary keys must be strings"; let it.
            Py_DECREF(result);
            return Step::kFallback;
        }

        PyObject* converted = nullptr;
        const Step step = cast_element(value, op, &converted);
        if (step != Step::kOk) {
            Py_XDECREF(converted);
            Py_DECREF(result);
            return step;
        }

        const int rc = PyDict_SetItem(result, key, converted);
        Py_DECREF(converted);
        if (rc < 0) {
            Py_DECREF(result);
            return Step::kError;
        }
    }

    *out = result;
    return Step::kOk;
}

// Container validation for ListFacet, SetFacet, and TupleFacet.
//
// The three facets differ only in what they accept and what they produce
// (facets.py):
//
//   ListFacet   accepts (list, tuple)        -> list
//   SetFacet    accepts (list, tuple, set)   -> set
//   TupleFacet  accepts (list, tuple, set)   -> tuple
//
// Element casting is identical across all three, so it is written once here.
// Item-count bounds are NOT applied in this function: they belong to seal, which
// runs after every element has cast, and are handled by check_item_counts so the
// ordering matches facets.py.
//
// A set input is deliberately refused for every container. Iterating a set has
// no defined order, so a Set/Tuple built from one could differ run to run under
// hash randomisation -- and for TupleFacet that ordering is observable in the
// result. Python has the same non-determinism, but reproducing it here would
// mean the native and Python paths could disagree on a given run while both
// being "correct", which is untestable. Deferring keeps one source of truth.
Step cast_container(PyObject* raw, const FieldOp& op, PyObject** out) {
    if (op.container == ContainerKind::Dict) return cast_dict(raw, op, out);

    const bool is_list = PyList_CheckExact(raw);
    const bool is_tuple = PyTuple_CheckExact(raw);
    if (!is_list && !is_tuple) return Step::kFallback;

    const Py_ssize_t len = is_list ? PyList_GET_SIZE(raw) : PyTuple_GET_SIZE(raw);

    // Cast every element into a temporary list first. Building the final
    // container up front would mean a half-filled set or tuple to unwind on the
    // first element that defers.
    PyObject* staged = PyList_New(len);
    if (!staged) return Step::kError;

    for (Py_ssize_t i = 0; i < len; ++i) {
        // Borrowed; the source container owns it and outlives this loop.
        PyObject* item = is_list ? PyList_GET_ITEM(raw, i) : PyTuple_GET_ITEM(raw, i);

        PyObject* converted = nullptr;
        const Step step = cast_element(item, op, &converted);
        if (step != Step::kOk) {
            Py_XDECREF(converted);
            Py_DECREF(staged);
            return step;
        }
        PyList_SET_ITEM(staged, i, converted);  // steals the reference
    }

    switch (op.container) {
        case ContainerKind::List:
            *out = staged;
            return Step::kOk;
        case ContainerKind::Set: {
            // PySet_New raises TypeError on an unhashable element -- exactly what
            // Python's set(value) does, so the failure is deferred, not reported.
            PyObject* as_set = PySet_New(staged);
            Py_DECREF(staged);
            if (!as_set) {
                PyErr_Clear();
                return Step::kFallback;
            }
            *out = as_set;
            return Step::kOk;
        }
        case ContainerKind::Tuple: {
            PyObject* as_tuple = PyList_AsTuple(staged);
            Py_DECREF(staged);
            if (!as_tuple) return Step::kError;
            *out = as_tuple;
            return Step::kOk;
        }
        default:
            Py_DECREF(staged);
            return Step::kFallback;
    }
}

}  // namespace

FieldPlan::~FieldPlan() {
    for (auto& op : ops_) {
        Py_XDECREF(op.name);
        Py_XDECREF(op.default_value);
        Py_XDECREF(op.min_value);
        Py_XDECREF(op.max_value);
        Py_XDECREF(op.multiple_of);
        Py_XDECREF(op.choices);
        Py_XDECREF(op.enum_cls);
        Py_XDECREF(op.enum_by_value);
        Py_XDECREF(op.enum_by_name);
        Py_XDECREF(op.pattern);
        // Releases the sub-plan. op.nested_plan is a non-owning view into this
        // same object and must not be touched after it.
        Py_XDECREF(op.nested_plan_obj);
    }
}

void FieldPlan::add(const FieldSpec& s) {
    // kFieldHasDefault promises default_value is a real object. execute() stores
    // it with PyDict_SetItem, which segfaults on NULL rather than raising, so the
    // invariant is asserted here where the failure is still attributable. Note
    // that `default=None` is a real default and must arrive as Py_None, not null.
    assert(!(s.flags & kFieldHasDefault) || s.default_value != nullptr);
    // A Choice/Enum/Nested op without its data could never match anything, so it
    // would silently reject every payload instead of accelerating it. Fail here,
    // where the plan is being built, rather than at the first request.
    assert((s.code != TypeCode::Choice) || s.choices != nullptr);
    assert((s.code != TypeCode::Enum) ||
           (s.enum_cls != nullptr && s.enum_by_value != nullptr && s.enum_by_name != nullptr));
    assert((s.code != TypeCode::Nested) || (s.nested_plan != nullptr && s.nested_plan_obj != nullptr));
    // The Dict container carries its bound in max_keys, not max_items, because
    // DictFacet spells it that way and checks it in cast rather than seal.
    assert((s.container != ContainerKind::Dict) || s.min_items < 0);

    FieldOp op;
    op.name = Py_NewRef(s.name);
    op.code = s.code;
    op.container = s.container;
    op.flags = s.flags;
    op.default_value = s.default_value ? Py_NewRef(s.default_value) : nullptr;
    op.min_value = s.min_value ? Py_NewRef(s.min_value) : nullptr;
    op.max_value = s.max_value ? Py_NewRef(s.max_value) : nullptr;
    op.multiple_of = s.multiple_of ? Py_NewRef(s.multiple_of) : nullptr;
    op.choices = s.choices ? Py_NewRef(s.choices) : nullptr;
    op.enum_cls = s.enum_cls ? Py_NewRef(s.enum_cls) : nullptr;
    op.enum_by_value = s.enum_by_value ? Py_NewRef(s.enum_by_value) : nullptr;
    op.enum_by_name = s.enum_by_name ? Py_NewRef(s.enum_by_name) : nullptr;
    op.pattern = s.pattern ? Py_NewRef(s.pattern) : nullptr;
    op.nested_plan_obj = s.nested_plan_obj ? Py_NewRef(s.nested_plan_obj) : nullptr;
    op.nested_plan = s.nested_plan;
    op.min_length = s.min_length;
    op.max_length = s.max_length;
    op.min_items = s.min_items;
    op.max_items = s.max_items;
    op.max_digits = s.max_digits;
    op.decimal_places = s.decimal_places;
    op.max_keys = s.max_keys;
    ops_.push_back(op);
}

int FieldPlan::execute(PyObject* payload, PyObject** validated) const {
    // Exactly dict, not a subclass: MultiDict and FormData need the alternate
    // key handling ("field[]", flat-list extraction) that lives in Python.
    if (!PyDict_CheckExact(payload)) return 0;

    PyObject* out = PyDict_New();
    if (!out) return -1;

    for (const auto& op : ops_) {
        // Interned key -> the dict lookup hits its pointer-equality fast path.
        PyObject* raw = PyDict_GetItemWithError(payload, op.name);
        if (!raw) {
            if (PyErr_Occurred()) {
                Py_DECREF(out);
                return -1;
            }
            // Missing. This order is load-bearing (05 section 3.4): default is
            // consulted BEFORE required, so a field that is both required and
            // defaulted uses the default rather than erroring.
            if (op.flags & kFieldHasDefault) {
                if (PyDict_SetItem(out, op.name, op.default_value) < 0) {
                    Py_DECREF(out);
                    return -1;
                }
                continue;
            }
            if (op.flags & kFieldRequired) {
                Py_DECREF(out);
                return 0;  // Python produces the "required" error
            }
            if (op.flags & kFieldAllowNull) {
                if (PyDict_SetItem(out, op.name, Py_None) < 0) {
                    Py_DECREF(out);
                    return -1;
                }
                continue;
            }
            continue;  // absent and optional: skipped silently
        }

        // An explicit None is NOT interchangeable with a missing key
        // (05 section 3.5) -- they follow different resolution paths.
        if (raw == Py_None) {
            if (op.flags & kFieldAllowNull) {
                if (PyDict_SetItem(out, op.name, Py_None) < 0) {
                    Py_DECREF(out);
                    return -1;
                }
                continue;
            }
            Py_DECREF(out);
            return 0;  // Python produces the "not_null" error
        }

        PyObject* value = nullptr;
        Step step;

        // Cast phase. A container dispatches on its element type and produces
        // the shape its facet declares; a scalar dispatches on its own code.
        if (op.container != ContainerKind::None) {
            step = cast_container(raw, op, &value);
        } else {
            switch (op.code) {
                case TypeCode::Int:
                    step = cast_int(raw, &value);
                    break;
                case TypeCode::Str:
                    step = cast_text(raw, op.flags, &value);
                    break;
                case TypeCode::Float:
                    step = cast_float(raw, &value);
                    break;
                case TypeCode::Bool:
                    step = cast_bool(raw, &value);
                    break;
                case TypeCode::Uuid:
                    step = cast_uuid(raw, &value);
                    break;
                case TypeCode::Date:
                    step = cast_iso(raw, ctors().date_type, ctors().date_fromisoformat, &value);
                    break;
                case TypeCode::DateTime:
                    step = cast_iso(raw, ctors().datetime_type, ctors().datetime_fromisoformat, &value);
                    break;
                case TypeCode::Time:
                    step = cast_iso(raw, ctors().time_type, ctors().time_fromisoformat, &value);
                    break;
                case TypeCode::Decimal:
                    step = cast_decimal(raw, &value);
                    break;
                case TypeCode::Duration:
                    step = cast_duration(raw, &value);
                    break;
                case TypeCode::Enum:
                    step = cast_enum(raw, op, &value);
                    break;
                case TypeCode::Bytes:
                    step = cast_bytes(raw, &value);
                    break;
                case TypeCode::Nested:
                    step = cast_nested(raw, op, &value);
                    break;
                case TypeCode::Choice:
                    // ChoiceFacet.cast is identity; the whole constraint is in seal.
                    value = Py_NewRef(raw);
                    step = Step::kOk;
                    break;
                default:
                    step = Step::kFallback;
                    break;
            }
        }

        // Seal phase: apply type-specific constraints in the order facets.py does.
        if (step == Step::kOk) {
            if (op.container != ContainerKind::None) {
                // DictFacet enforces its bound (max_keys) during cast, and has no
                // seal-phase count check at all; the sequence containers check
                // theirs here.
                if (op.container != ContainerKind::Dict) step = check_item_counts(op, value);
            } else {
                switch (op.code) {
                    case TypeCode::Str:
                        // Order is observable: TextFacet.seal checks lengths
                        // before the pattern, so the first violation Python
                        // reports is the one this defers on.
                        step = check_lengths(op, value);
                        if (step == Step::kOk) step = check_pattern(op, value);
                        break;
                    case TypeCode::Bytes:
                        step = check_byte_lengths(op, value);
                        break;
                    case TypeCode::Int:
                    case TypeCode::Float:
                        step = check_bounds(op, value);
                        if (step == Step::kOk) step = check_multiple_of(op, value);
                        break;
                    case TypeCode::Decimal:
                        step = check_bounds(op, value);
                        if (step == Step::kOk) step = check_decimal_precision(op, value);
                        break;
                    case TypeCode::Choice:
                        step = seal_choice(op, value);
                        break;
                    default:
                        // Date/Time/DateTime/Bool/Uuid/Duration/Enum/Nested carry
                        // no seal constraints: their facets validate entirely
                        // during cast.
                        break;
                }
            }
        }

        // Single release path for `value`. An earlier version decref'd it inside
        // the constraint branch *and* again here, which double-freed whenever a
        // bounds comparison failed -- a segfault, caught by the mail config
        // tests rather than by anything in tests/dataengine.
        if (step != Step::kOk) {
            Py_XDECREF(value);
            Py_DECREF(out);
            return step == Step::kError ? -1 : 0;
        }

        const int rc = PyDict_SetItem(out, op.name, value);
        Py_DECREF(value);
        if (rc < 0) {
            Py_DECREF(out);
            return -1;
        }
    }

    *validated = out;
    return 1;
}

}  // namespace aq
