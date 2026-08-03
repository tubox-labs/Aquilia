// request_ctx.cpp -- RequestContext is a plain aggregate of PyRef slots
// (request_ctx.hpp) and its Python surface is bound in module.cpp, so there is
// no out-of-line logic to define here.
//
// This translation unit exists so the class has a home in the build if slot
// initialisation or reset logic ever needs to move out of the header, and so
// request_ctx.hpp is compiled standalone -- catching any header that only
// happens to work because module.cpp included something first.
#include "request_ctx.hpp"

namespace aq {

// Fail the build if the slot layout changes without the bindings following. Every
// slot in module.cpp's AQ_SLOT list must appear here and vice versa.
static_assert(sizeof(RequestContext) == 7 * sizeof(PyRef),
              "RequestContext slot count changed -- update the AQ_SLOT bindings "
              "in module.cpp and RequestCtx.__slots__ in controller/base.py");

static_assert(sizeof(PyRef) == sizeof(void*),
              "PyRef must stay a single pointer: RequestContext is allocated per "
              "request and any padding here is paid on every request");

}  // namespace aq
