// request_ctx.hpp -- native RequestContext with fixed slots.
//
// Targets the measured RequestCtx.__setattr__ cost: ~24 attribute writes per
// request through a try/except override, 1.26us total (7.6% of a request).
// nanobind's def_rw installs a data descriptor on the type, so a write to a
// declared slot never enters __setattr__ at all -- it is a direct field store.
//
// The Python-visible contract is unchanged. RequestCtx subclasses this type and
// keeps its properties, effect helpers, and the `_extra` escape hatch that its
// docstring advertises for middleware and plugins.
//
// Phase 9F.
#pragma once

#include <Python.h>

#include <cstddef>
#include <type_traits>

namespace aq {

/// Owning PyObject* reference. Deliberately not nb::object: this header is
/// included by request_ctx.cpp only, and a minimal wrapper keeps the ownership
/// rules explicit at every assignment.
///
/// Copy increfs, move steals, destruction decrefs. Uses Py_XINCREF/Py_XDECREF
/// throughout because every slot legitimately starts as nullptr (Python None is
/// a distinct, non-null value).
class PyRef {
public:
    PyRef() noexcept = default;

    /// @param steal When true, adopt @p p's existing reference instead of
    ///              taking a new one.
    explicit PyRef(PyObject* p, bool steal = false) noexcept : p_(p) {
        if (!steal) Py_XINCREF(p_);
    }

    PyRef(const PyRef& o) noexcept : p_(o.p_) { Py_XINCREF(p_); }

    PyRef(PyRef&& o) noexcept : p_(o.p_) { o.p_ = nullptr; }

    PyRef& operator=(const PyRef& o) noexcept {
        if (this != &o) {
            PyObject* old = p_;
            p_ = o.p_;
            Py_XINCREF(p_);
            Py_XDECREF(old);  // decref last: self-assignment via alias stays safe
        }
        return *this;
    }

    PyRef& operator=(PyRef&& o) noexcept {
        if (this != &o) {
            PyObject* old = p_;
            p_ = o.p_;
            o.p_ = nullptr;
            Py_XDECREF(old);
        }
        return *this;
    }

    ~PyRef() noexcept { Py_XDECREF(p_); }

    [[nodiscard]] PyObject* get() const noexcept { return p_; }
    [[nodiscard]] bool empty() const noexcept { return p_ == nullptr; }

private:
    PyObject* p_ = nullptr;
};

static_assert(sizeof(PyRef) == sizeof(PyObject*),
              "PyRef must stay pointer-sized: RequestContext::slots() reinterprets "
              "the slot block as a PyObject* array for tp_traverse/tp_clear.");

/// Fixed-slot request context.
///
/// Slots mirror the seven real fields of RequestCtx. There is deliberately no
/// `extra` slot: nanobind's `dynamic_attr()` already gives instances a
/// `__dict__`, which *is* the dynamic-attribute store that RequestCtx exposes as
/// `_extra`. A separate slot would be a second, divergent store -- an attribute
/// written via `ctx.foo = 1` would land in `__dict__` while `ctx._extra` read
/// the empty slot, which is not what the pure-Python class does.
struct RequestContext {
    PyRef request;
    PyRef identity;
    PyRef session;
    PyRef auth;
    PyRef container;
    PyRef state;
    PyRef request_id;

    static constexpr std::size_t kSlotCount = 7;

    /// The slot block viewed as a plain ``PyObject*`` array.
    ///
    /// Exists for ``tp_traverse``/``tp_clear``. nanobind's own traverse visits
    /// the ``dynamic_attr`` dict and the type, but it cannot see C++ fields --
    /// so before this existed, a cycle running *through a slot*
    /// (``ctx.state = {"ctx": ctx}``) was invisible to the collector and the
    /// instance leaked forever. That was one leaked RequestCtx per request.
    ///
    /// Safe because the slots are consecutive, pointer-sized, and
    /// standard-layout -- all three asserted, so a future edit that breaks the
    /// assumption fails to compile rather than corrupting the heap.
    [[nodiscard]] PyObject** slots() noexcept { return reinterpret_cast<PyObject**>(this); }
};

static_assert(std::is_standard_layout_v<RequestContext>,
              "RequestContext::slots() requires standard layout for the "
              "reinterpret_cast to the first member to be well-defined.");
static_assert(sizeof(RequestContext) == RequestContext::kSlotCount * sizeof(PyObject*),
              "RequestContext gained padding or a non-PyRef member -- slots() "
              "would hand tp_traverse something that is not a PyObject*.");

}  // namespace aq
