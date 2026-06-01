// Narrow the `level` field to `uint8_t` since its true range is [0, 255].
// The compiler can never legally make this change: struct field width is
// an ABI invariant that may be observed by external code, serialized to
// disk, or shared via mmap.  Only a human author can densify it.
//
// Result: the array shrinks from 64 MB to 1 MB.  The sum reduction
// auto-vectorizes (16-byte NEON / 32-byte AVX2 loads) over uint8_t lanes,
// turning a memory-bound scan into a cache-resident one.
#include <stdint.h>

long long sum_narrow_ho_ds3_v004(uint8_t *levels, long n);

long long fast_ho_ds3_v004(uint8_t *levels, long n) {
    return sum_narrow_ho_ds3_v004(levels, n);
}
