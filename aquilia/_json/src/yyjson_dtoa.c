/*
 * yyjson_dtoa.c -- expose yyjson's double formatter as a public symbol.
 *
 * Why this file exists
 * --------------------
 * The encoder needs shortest-round-trip double formatting that writes into a
 * caller-supplied buffer. Two obvious options were measured and rejected:
 *
 *   * PyOS_double_to_string. Correct, but mallocs and frees a string per value.
 *     On a float-heavy 100KB payload that allocation traffic dominated: 380us
 *     against msgspec's 118us for the same 5000 values.
 *
 *   * yyjson_mut_val_write_opts. Also correct, and it uses the fast formatter
 *     internally -- but it too returns a heap string, so it trades one malloc
 *     for another.
 *
 * yyjson already contains the algorithm we want (a Schubfach/Ryu-class shortest
 * representation writer) in `write_f64_raw`, which writes into a caller buffer
 * and allocates nothing. It is `static_inline`, so it is not linkable from
 * another translation unit.
 *
 * Rather than copy several hundred lines of numerically delicate code into this
 * repository -- where it would silently diverge from upstream on the next
 * yyjson bump -- this file #includes yyjson.c and publishes a thin wrapper.
 * The vendored source stays byte-identical to the upstream release, and the
 * only thing we own is the four-line shim below.
 *
 * The cost is that yyjson.c is compiled twice in this target; the linker keeps
 * one copy of the external symbols because the second inclusion is confined to
 * this file's translation unit and everything it defines is static.
 */

#include "yyjson_dtoa.h"

/* Pull in the implementation so the static_inline writer is visible here. */
#include "yyjson.c"

char *aq_yyjson_write_double(double v, char *buf) {
    /* write_f64_raw takes the raw bit pattern rather than the double, matching
     * how yyjson stores reals internally. */
    u64 raw;
    memcpy(&raw, &v, sizeof raw);
    /* YYJSON_WRITE_NOFLAG: no INF/NAN literals. The caller has already rejected
     * non-finite values, because JSON cannot represent them. */
    return (char *)write_f64_raw((u8 *)buf, raw, YYJSON_WRITE_NOFLAG);
}
