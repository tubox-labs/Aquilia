// convert.hpp -- scalar conversions, delegating to CPython wherever CPython wins.
//
// The conversion policy here follows the measurement in
// docs/models-engine/02-performance-audit.md section 3 exactly, and it is the
// opposite of the obvious design. Six of eight scalar conversions cost LESS
// than one boundary crossing because CPython's fromisoformat/int/float are
// already C, so this layer calls straight back into them. Only UUID (354 ns,
// pure-Python __init__) and JSON are slow enough to be worth native code.
//
// The engine's value is therefore not in converting values faster -- it is in
// not executing Python bytecode per field around each conversion. That is what
// rowplan/fieldplan deliver; this file just makes each individual conversion no
// worse than Python's.
//
// Re-entrancy: the only Python called from here is a small set of *built-in C
// constructors* captured once at module init. No user code, no __init__
// overrides, no descriptors. The plan compilers guarantee a plan containing user
// code never compiles, so this stays bounded.
#pragma once

#include <Python.h>

#include "typecode.hpp"

namespace aq {

// CPython constructors captured once at module init, plus the interned attribute
// names the UUID fast path writes.
struct Constructors {
    PyObject* date_fromisoformat = nullptr;
    PyObject* datetime_fromisoformat = nullptr;
    PyObject* time_fromisoformat = nullptr;
    // The types themselves, for the "already the right type" fast paths in
    // fieldplan, where a payload may arrive pre-parsed.
    PyTypeObject* date_type = nullptr;
    PyTypeObject* datetime_type = nullptr;
    PyTypeObject* time_type = nullptr;
    // timedelta, for DurationFacet. Only the type is needed: the numeric branch
    // constructs through it directly and the string branches defer to Python.
    PyTypeObject* timedelta_type = nullptr;
    PyObject* decimal_type = nullptr;
    PyObject* json_loads = nullptr;
    PyTypeObject* uuid_type = nullptr;
    PyObject* safe_uuid_unknown = nullptr;
    PyObject* str_int = nullptr;      // interned "int"
    PyObject* str_is_safe = nullptr;  // interned "is_safe"
    PyObject* str_search = nullptr;   // interned "search", for re.Pattern.search
    // The two __slots__ member descriptors, cached so the UUID fast path can
    // drive tp_descr_set directly instead of paying an MRO walk plus a type-dict
    // lookup per attribute per parse.
    PyObject* uuid_int_descr = nullptr;
    PyObject* uuid_is_safe_descr = nullptr;
    bool ready = false;
};

// Import and cache the constructors. Returns false with a Python error set.
// Called once from module init; every conversion assumes it succeeded.
bool init_constructors();

const Constructors& ctors();

// Convert one raw row/payload value according to `code`.
//
// Returns a NEW reference, or nullptr with a Python error set. A nullptr return
// aborts the whole batch and the caller re-runs it in Python, so the error that
// ultimately surfaces to the user is produced by the same Python code as today
// -- identical message, fault code, and traceback.
PyObject* convert(TypeCode code, PyObject* raw);

// Convert one raw DB value the way Model.from_row's field.to_python does.
//
// This is deliberately SEPARATE from convert(): the ORM's to_python methods are
// not the same function as the contracts' facet casts, and several differ in
// ways that would be silent data corruption if merged.
//
//   * DateField/DateTimeField/TimeField/DecimalField/UUIDField map a blank or
//     whitespace-only string to None, because a blank text column and a real
//     NULL both mean "no value" (fields_module.py).
//   * DecimalField is Decimal(str(value)) -- the str() is load-bearing for
//     float input.
//   * JSONField returns an unparseable string AS-IS rather than raising.
//
// Returns a new reference, nullptr with an error set on a genuine failure, or
// nullptr with NO error set when the caller must fall back to Python.
PyObject* convert_hydrate(TypeCode code, PyObject* raw);

// Build a uuid.UUID from a string without re-entering its pure-Python __init__.
// Exposed separately so the M3 gate can measure it directly. Returns nullptr
// WITHOUT setting an error when the string is outside the narrow grammar
// uuid_parse accepts -- the caller must then fall back to uuid.UUID itself.
PyObject* uuid_from_string(PyObject* s);

}  // namespace aq
