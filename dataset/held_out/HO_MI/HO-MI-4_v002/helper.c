#include <stdint.h>

// Externally-visible state shared across decode calls.  In real zstd
// this is a running checksum field in the decoder context struct;
// here it is an extern variable so the compiler cannot dead-code-
// eliminate the per-symbol state update in slow.c / fast.c.
uint64_t ho_mi4_state_v002 = 0;
