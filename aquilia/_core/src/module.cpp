// module.cpp -- the only translation unit that includes nanobind.
//
// Thin translation shell: no business rules live here. Every entry point holds
// the GIL because it produces or consumes Python objects; releasing it around
// work this short would cost more than the work itself.
//
// Phase 9B/9D/9F.
#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/string_view.h>
#include <nanobind/stl/vector.h>

#include <string>

#include "interner.hpp"
#include "request_ctx.hpp"
#include "router.hpp"

namespace nb = nanobind;

namespace {

/// Returned by Router.match when the native matcher cannot decide a path and
/// the caller must re-run the Python matcher. A unique sentinel object, so the
/// Python side compares with `is` rather than truth-testing an ambiguous value.
/// The "native matcher declines to decide" sentinel is ``NotImplemented``.
///
/// A dedicated nb::class_ was the obvious choice and the wrong one: it adds a
/// type, an instance, and a __repr__ to the module, all of which outlive
/// nanobind's shutdown leak check and get reported. ``NotImplemented`` is an
/// immortal CPython singleton whose documented meaning is precisely "this
/// operation declines to answer; ask someone else", it can never be confused
/// with a miss (None) or a hit (tuple), and it costs no allocation.
PyObject* defer_sentinel() noexcept { return Py_NotImplemented; }

/// Build a Python str from raw bytes.
///
/// Segment boundaries always fall on '/' (0x2F), which is never a UTF-8
/// continuation byte, so a segment can never split a codepoint. Decoding is
/// still strict: a path carrying invalid UTF-8 raises here exactly as the
/// Python matcher's own str operations would.
nb::object make_str(const char* data, std::size_t len) {
    PyObject* s = PyUnicode_DecodeUTF8(data, static_cast<Py_ssize_t>(len), nullptr);
    if (s == nullptr) throw nb::python_error();
    return nb::steal(s);
}

/// Convert a captured segment to int via PyLong_FromString, which is CPython's
/// own int() parser. The router has already confirmed the ASCII fast-path shape;
/// anything outside it was reported as Defer and never reaches here.
nb::object make_int(const char* data, std::size_t len) {
    const std::string buf(data, len);  // PyLong_FromString needs NUL termination
    PyObject* v = PyLong_FromString(buf.c_str(), nullptr, 10);
    if (v == nullptr) throw nb::python_error();
    return nb::steal(v);
}

nb::object make_float(const char* data, std::size_t len) {
    nb::object s = make_str(data, len);
    PyObject* v = PyFloat_FromString(s.ptr());
    if (v == nullptr) throw nb::python_error();
    return nb::steal(v);
}

// -- RequestContext slot accessors -----------------------------------------
// def_prop_rw over PyRef rather than def_rw: nanobind needs a type caster to
// bind a field directly, and an explicit getter/setter pair keeps the incref
// rules visible at each use. Both are still data descriptors on the type, so a
// slot write is a direct field store and never enters __setattr__.

nb::object slot_get(const aq::PyRef& r) {
    return r.empty() ? nb::none() : nb::borrow(r.get());
}

// Takes nb::object, not nb::handle: every one of these slots legitimately holds
// None (an unauthenticated request has no identity, a sessionless one no
// session). nb::object alone is not enough -- nanobind rejects None at the
// binding boundary unless the argument is marked .none(), and that mark must be
// scoped with for_setter so it does not disturb the nullary getter.
void slot_set(aq::PyRef& r, nb::object v) { r = aq::PyRef(v.ptr()); }

#define AQ_SLOT(name)                                                            \
    def_prop_rw(                                                                 \
        #name, [](const aq::RequestContext& c) { return slot_get(c.name); },      \
        [](aq::RequestContext& c, nb::object v) { slot_set(c.name, std::move(v)); }, \
        nb::for_setter(nb::arg("value").none()))

void bind_router(nb::module_& m) {
    m.attr("DEFER") = nb::borrow(defer_sentinel());

    nb::enum_<aq::ParamKind>(m, "ParamKind")
        .value("STR", aq::ParamKind::Str)
        .value("INT", aq::ParamKind::Int)
        .value("FLOAT", aq::ParamKind::Float);

    nb::class_<aq::Router>(m, "Router", nb::is_final())
        .def(nb::init<>())
        .def("add_static", &aq::Router::add_static, nb::arg("method"), nb::arg("path"),
             nb::arg("route_id"),
             "Register a parameter-free path. False means conflict: caller keeps "
             "the method on the Python path.")
        .def(
            "add_route",
            [](aq::Router& self, std::string_view method, std::string_view path,
               const nb::dict& param_kinds, aq::RouteId route_id) {
                std::unordered_map<std::string, aq::ParamKind> kinds;
                for (auto [k, v] : param_kinds) {
                    kinds.emplace(nb::cast<std::string>(k), nb::cast<aq::ParamKind>(v));
                }
                return self.add_route(method, path, kinds, route_id);
            },
            nb::arg("method"), nb::arg("path"), nb::arg("param_kinds"), nb::arg("route_id"),
            "Register a parameterised path. False means not natively "
            "representable: caller keeps the method on the Python path.")
        .def("freeze", &aq::Router::freeze, "Flatten the trie. One-way; idempotent.")
        .def_prop_ro("frozen", &aq::Router::frozen)
        .def_prop_ro("node_count", &aq::Router::node_count)
        .def_prop_ro("static_count", &aq::Router::static_count)
        .def(
            "match",
            [](const aq::Router& self, std::string_view method, std::string_view path) -> nb::object {
                const aq::MatchResult r = self.match(method, path);
                if (r.status == aq::MatchStatus::Miss) return nb::none();
                if (r.status == aq::MatchStatus::Defer) {
                    return nb::borrow(defer_sentinel());
                }
                nb::dict params;
                const std::string_view names = self.name_bytes();
                for (std::uint32_t i = 0; i < r.param_count; ++i) {
                    const aq::CapturedParam& p = r.params[i];
                    nb::object key = make_str(names.data() + p.name_off, p.name_len);
                    const char* vp = path.data() + p.value_off;
                    nb::object val;
                    switch (p.kind) {
                        case aq::ParamKind::Int: val = make_int(vp, p.value_len); break;
                        case aq::ParamKind::Float: val = make_float(vp, p.value_len); break;
                        default: val = make_str(vp, p.value_len); break;
                    }
                    params[key] = val;
                }
                return nb::make_tuple(r.route_id, params);
            },
            nb::arg("method"), nb::arg("path"),
            "Match a path. None = miss, DEFER = fall back to Python, "
            "(route_id, params) = hit.")
        .def("allowed_methods", &aq::Router::allowed_methods, nb::arg("path"),
             "Methods accepting this path. 405 path only.");
}

void bind_request_ctx(nb::module_& m) {
    // dynamic_attr(): unknown attribute writes land in the instance __dict__
    // instead of raising, so middleware that attaches ad-hoc attributes keeps
    // working. Declared slots resolve through their descriptors first and never
    // touch the dict.
    nb::class_<aq::RequestContext>(m, "RequestContext", nb::dynamic_attr())
        .def(nb::init<>())
        .AQ_SLOT(request)
        .AQ_SLOT(identity)
        .AQ_SLOT(session)
        .AQ_SLOT(auth)
        .AQ_SLOT(container)
        .AQ_SLOT(state)
        .AQ_SLOT(request_id);
}

void bind_interner(nb::module_& m) {
    // Diagnostics only: nothing on the hot path calls into this from Python.
    nb::class_<aq::Interner>(m, "Interner", nb::is_final())
        .def(nb::init<>())
        .def("intern", &aq::Interner::intern, nb::arg("s"))
        .def("lookup", &aq::Interner::lookup, nb::arg("s"))
        .def("get", &aq::Interner::get, nb::arg("id"))
        .def("__len__", &aq::Interner::size);
}

}  // namespace

NB_MODULE(_core, m) {
    m.doc() = "Aquilia native core engine (router, request context).";
    m.attr("NO_INTERN") = aq::NO_INTERN;

    /// Empty call used to measure the nanobind entry-point overhead that every
    /// other binding pays. See benchmarks/engine/call_overhead.py -- this number
    /// decides whether a native replacement for a Python dict lookup can win.
    m.def("noop", []() {}, "No-op. Measures per-call binding overhead.");

    bind_interner(m);
    bind_router(m);
    bind_request_ctx(m);
}
