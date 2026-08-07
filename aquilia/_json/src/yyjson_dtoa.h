/*
 * yyjson_dtoa.h -- shortest-round-trip double formatting, no allocation.
 *
 * Implemented in yyjson_dtoa.c by delegating to yyjson's own formatter. See
 * that file for why the implementation is a shim rather than a copy.
 */
#ifndef AQUILIA_JSON_YYJSON_DTOA_H
#define AQUILIA_JSON_YYJSON_DTOA_H

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Bytes that aq_yyjson_write_double may write.
 *
 * yyjson documents 32 as the requirement for its number writer. The longest
 * output in practice is a 17-significant-digit value with sign and exponent
 * (e.g. "-1.2345678901234567e-308", 24 bytes), so 32 leaves margin.
 */
#define AQ_DTOA_BUF_SIZE 32

/*
 * Write `v` to `buf` as the shortest decimal string that reparses to exactly
 * `v`.
 *
 * The caller must supply at least AQ_DTOA_BUF_SIZE bytes and must have already
 * rejected NaN and infinity -- JSON has no representation for either, and this
 * function does not check.
 *
 * Returns a pointer one past the last byte written. Nothing is allocated and no
 * NUL terminator is appended.
 */
char *aq_yyjson_write_double(double v, char *buf);

#ifdef __cplusplus
}
#endif

#endif /* AQUILIA_JSON_YYJSON_DTOA_H */
