// rowplan.hpp -- compiled hydration plan (docs/models-engine/04).
//
// Replaces the per-row body of Model.from_row for eligible plans only. Row shape
// is invariant within a result set (01 section 3.2) -- one query, one
// cursor.description -- so the column->field mapping is resolved once per query
// and replayed per row, rather than re-dispatched per column per row.
//
// What this removes per field, against base.py's loop:
//
//   col_to_attr.get(key)               ~8 ns   dict lookup
//   field.to_python(raw)               30-100 ns of Python dispatch
//   isinstance(field, ForeignKey)      ~16 ns  (B6)
//   setattr -> descriptor __set__      ~114 ns (B3)
//   the deferred setcomp, per row      ~148 ns (B4)
//
// Writing instance.__dict__ directly is not a shortcut: Field.__set__ is exactly
// `instance.__dict__[attr] = value` (fields_module.py). The descriptor stays in
// place for class-level access, which is public API for query building; only the
// per-write dispatch is skipped, and only for plans proven to contain no custom
// __set__.
//
// THE HIGHEST-SEVERITY INVARIANT IS _original_values (04 section 3.2). save()
// diffs against it to build minimal UPDATE statements. If it holds the wrong
// values, save() either writes columns that did not change or -- worse, and
// silently -- skips columns that did. The snapshot must contain the CONVERTED
// value, and exactly the attributes that were actually set.
#pragma once

#include <Python.h>

#include <cstdint>
#include <vector>

#include "typecode.hpp"

namespace aq {

// One compiled column, in row order.
struct ColumnOp {
    PyObject* key = nullptr;   // interned row key (column or attr name)
    PyObject* attr = nullptr;  // interned instance-dict key
    TypeCode code = TypeCode::Unsupported;
    std::uint8_t flags = kFlagNone;
};

class RowPlan {
public:
    RowPlan() = default;
    ~RowPlan();

    RowPlan(const RowPlan&) = delete;
    RowPlan& operator=(const RowPlan&) = delete;

    void set_model(PyObject* model_cls, PyObject* related_not_loaded, PyObject* model_name);
    void add(PyObject* key, PyObject* attr, TypeCode code, std::uint8_t flags);

    // Hydrate a batch.
    //
    // Returns a new list reference on success, or nullptr. When nullptr is
    // returned WITHOUT a Python error set, the caller must fall back to
    // Model.from_row for the whole batch -- never a partial result, so a batch
    // either completes or produces nothing (04 section 7).
    PyObject* execute(PyObject* rows) const;

    std::size_t size() const { return ops_.size(); }

private:
    std::vector<ColumnOp> ops_;
    PyObject* model_cls_ = nullptr;
    PyObject* model_new_ = nullptr;           // cls.__new__, resolved once
    PyObject* related_not_loaded_ = nullptr;  // the RelatedNotLoaded class
    PyObject* model_name_ = nullptr;          // cls.__name__, for the FK sentinel
    PyObject* str_original_values_ = nullptr;
    PyObject* str_field_name_ = nullptr;
    PyObject* str_owner_model_name_ = nullptr;
};

}  // namespace aq
