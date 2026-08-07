// typecode.hpp -- the dispatch primitive shared by both plans.
//
// One uint8 switch replaces every isinstance chain in the hot loops. See
// docs/models-engine/03-engine-design.md section 4.
//
// Eligibility is decided per *plan*, not per field: if any column or field maps
// to Unsupported, the whole plan is rejected at compile time and the caller
// keeps the pure-Python path. A partially-native path would be a second
// implementation that could silently diverge, so there is deliberately no such
// thing as a partial plan.
#pragma once

#include <cstdint>

namespace aq {

enum class TypeCode : std::uint8_t {
    Passthrough = 0,  // value used as-is (str->str, int->int)
    Str = 1,
    Int = 2,
    Float = 3,
    Bool = 4,
    Date = 5,
    DateTime = 6,
    Time = 7,
    Decimal = 8,
    Uuid = 9,   // native hex parse -- the one measured per-value win
    Json = 10,  // native scan, Python object build
    Bytes = 11,
    Duration = 14,  // timedelta passthrough + numeric seconds
    Choice = 15,    // ChoiceFacet/LiteralFacet - frozenset membership
    Enum = 17,      // EnumFacet - value-then-name member lookup
    Nested = 18,    // NestedContractFacet - recursive sub-plan execution
    // Everything else -- custom field/facet, pipeline, validator, computed,
    // injected -- is NOT a type code. It marks the field ineligible and it is
    // escaped to Sigil.validate.
    Unsupported = 255,
};

// Container shape wrapping a TypeCode.
//
// This is a separate axis from TypeCode rather than a code per (container,
// element) pair. The pair encoding needed ListStr/ListInt/ListFloat/... and
// would have needed the same again for Set, Tuple, and Dict -- twenty-four
// codes to express six element types across four containers. Splitting the
// axes keeps it at six plus four, and a nested Contract composes with every
// container for free.
enum class ContainerKind : std::uint8_t {
    None = 0,   // scalar field; TypeCode applies to the value itself
    List = 1,   // ListFacet  -> Python list
    Set = 2,    // SetFacet   -> Python set (dedupes)
    Tuple = 3,  // TupleFacet -> Python tuple
    Dict = 4,   // DictFacet  -> Python dict; TypeCode applies to each *value*
};

// Per-column flags for RowPlan.
enum ColumnFlags : std::uint8_t {
    kFlagNone = 0,
    kFlagFkWrap = 1 << 0,   // wrap non-null values in RelatedNotLoaded
    kFlagNullable = 1 << 1,
};

// Per-field flags for FieldPlan. Each replaces a per-field isinstance or
// attribute read from sigil.py's validate loop (bottleneck B10); all are static
// at class-build time.
enum FieldFlags : std::uint8_t {
    kFieldNone = 0,
    kFieldRequired = 1 << 0,
    kFieldAllowNull = 1 << 1,
    kFieldHasDefault = 1 << 2,
    kFieldReadOnly = 1 << 3,
    // TextFacet.trim defaults to True, so a plan that ignored it would diverge
    // on almost every contract; TextFacet.seal rejects "" unless allow_blank.
    kFieldTrim = 1 << 4,
    kFieldAllowBlank = 1 << 5,
};

}  // namespace aq
