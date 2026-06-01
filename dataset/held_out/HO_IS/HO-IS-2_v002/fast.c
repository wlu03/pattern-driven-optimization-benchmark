#include <stdlib.h>
#include <string.h>

// FAST: 3-tier adaptive dispatch -- inspired by DuckDB's 2025 sort
// redesign ("Sorting Again", 2025-09-24, 10x speedup on sorted data).
// Step 1: scan first 64 elements to detect ascending/descending run.
//   - If fully ascending: nothing to do.
//   - If fully descending: in-place reverse, O(n).
// Step 2: if not a run, sample to detect small value range.
//   - If max - min <= 65536: counting sort, O(n + R).
// Step 3: otherwise fall back to qsort.
//
// Cite: DuckDB blog "Sorting Again" (2025-09-24).
void adaptive_sort_ho_is2_v002(int *arr, long n);

void fast_ho_is2_v002(int *arr, long n) {
    adaptive_sort_ho_is2_v002(arr, n);
}
