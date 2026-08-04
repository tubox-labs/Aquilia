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

#include "convert.hpp"
#include "fieldplan.hpp"
#include "typecode.hpp"

namespace nb = nanobind;

NB_MODULE(_dataengine, m) {
    m.doc() = "Aquilia native data engine: batch hydration and validation plans.";

    if (!aq::init_constructors()) {
        throw nb::python_error();
    }

    // Boundary-cost probe. benchmarks/models/boundary.py measures the crossing
    // against this, and the whole batch-vs-per-field design rests on that
    // number, so it ships rather than living in a scratch file.
    m.def("noop", []() {}, "Do nothing. Used to measure the Python<->native call cost.");

    // Direct conversion entry points. These exist for the M3 parity and gate
    // measurements, NOT as the production API -- a per-field native call is
    // refuted by 02 section 3, because the boundary costs more than six of the
    // eight conversions. Production traffic goes through the batch plans.
    m.def(
        "uuid_from_string",
        [](nb::object s) -> nb::object {
            PyObject* u = aq::uuid_from_string(s.ptr());
            if (!u) {
                if (PyErr_Occurred()) throw nb::python_error();
                // Outside the accepted grammar: the caller falls back to
                // uuid.UUID, which holds the authoritative semantics.
                return nb::none();
            }
            return nb::steal(u);
        },
        nb::arg("s"),
        "Parse a canonical UUID string. None means 'not handled -- use uuid.UUID'.");

    m.def(
        "convert",
        [](int code, nb::object raw) -> nb::object {
            PyObject* v = aq::convert(static_cast<aq::TypeCode>(code), raw.ptr());
            if (!v) throw nb::python_error();
            return nb::steal(v);
        },
        nb::arg("code"), nb::arg("raw").none(),
        "Convert one value by TypeCode. Parity-test entry point.");

    // TypeCode values, so the Python side builds plans against one definition
    // rather than a duplicated table that could drift.
    nb::module_ tc = m.def_submodule("TypeCode", "Type codes shared by both plans.");
    tc.attr("PASSTHROUGH") = static_cast<int>(aq::TypeCode::Passthrough);
    tc.attr("STR") = static_cast<int>(aq::TypeCode::Str);
    tc.attr("INT") = static_cast<int>(aq::TypeCode::Int);
    tc.attr("FLOAT") = static_cast<int>(aq::TypeCode::Float);
    tc.attr("BOOL") = static_cast<int>(aq::TypeCode::Bool);
    tc.attr("DATE") = static_cast<int>(aq::TypeCode::Date);
    tc.attr("DATETIME") = static_cast<int>(aq::TypeCode::DateTime);
    tc.attr("TIME") = static_cast<int>(aq::TypeCode::Time);
    tc.attr("DECIMAL") = static_cast<int>(aq::TypeCode::Decimal);
    tc.attr("UUID") = static_cast<int>(aq::TypeCode::Uuid);
    tc.attr("JSON") = static_cast<int>(aq::TypeCode::Json);
    tc.attr("BYTES") = static_cast<int>(aq::TypeCode::Bytes);
    tc.attr("UNSUPPORTED") = static_cast<int>(aq::TypeCode::Unsupported);

    // Field flag bits, same rationale as the type codes.
    nb::module_ ff = m.def_submodule("FieldFlags", "Per-field flag bits for FieldPlan.");
    ff.attr("REQUIRED") = static_cast<int>(aq::kFieldRequired);
    ff.attr("ALLOW_NULL") = static_cast<int>(aq::kFieldAllowNull);
    ff.attr("HAS_DEFAULT") = static_cast<int>(aq::kFieldHasDefault);
    ff.attr("READ_ONLY") = static_cast<int>(aq::kFieldReadOnly);
    ff.attr("TRIM") = static_cast<int>(aq::kFieldTrim);
    ff.attr("ALLOW_BLANK") = static_cast<int>(aq::kFieldAllowBlank);

    // ---------------------------------------------------------------------
    // FieldPlan
    // ---------------------------------------------------------------------
    nb::class_<aq::FieldPlan>(m, "FieldPlan")
        .def(nb::init<>())
        .def(
            "add",
            [](aq::FieldPlan& self, nb::object name, int code, int flags, nb::object default_value,
               nb::object min_value, nb::object max_value, Py_ssize_t min_length, Py_ssize_t max_length) {
                // default_value is passed through as-is, INCLUDING None:
                // `default=None` is a legitimate default, distinct from having
                // no default at all. Which of the two applies is carried by the
                // HAS_DEFAULT flag, not by the pointer being null. Collapsing
                // None to nullptr here stored a NULL in the op and segfaulted in
                // PyDict_SetItem on the first contract that used it.
                //
                // min_value/max_value are different: there, None genuinely means
                // "no bound", so the null mapping is correct.
                self.add(name.ptr(), static_cast<aq::TypeCode>(code), static_cast<std::uint8_t>(flags),
                         default_value.ptr(), min_value.is_none() ? nullptr : min_value.ptr(),
                         max_value.is_none() ? nullptr : max_value.ptr(), min_length, max_length);
            },
            nb::arg("name"), nb::arg("code"), nb::arg("flags"), nb::arg("default_value").none(),
            nb::arg("min_value").none(), nb::arg("max_value").none(), nb::arg("min_length"),
            nb::arg("max_length"),
            "Append one compiled field. Called once per field at plan-build time.")
        .def(
            "execute",
            [](const aq::FieldPlan& self, nb::object payload) -> nb::object {
                PyObject* validated = nullptr;
                const int rc = self.execute(payload.ptr(), &validated);
                if (rc < 0) throw nb::python_error();
                // None means "fall back": the caller re-runs the payload through
                // Sigil.validate, which owns the authoritative errors dict and
                // its localised messages.
                if (rc == 0) return nb::none();
                return nb::steal(validated);
            },
            nb::arg("payload"),
            "Validate a payload. Returns the validated dict, or None to fall back to Python.")
        .def("__len__", &aq::FieldPlan::size);
}
