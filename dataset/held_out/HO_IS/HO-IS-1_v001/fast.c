#include <stdlib.h>
#include <string.h>

// Counting sort: O(n + R) for n elements drawn from a small range R.
// For n=1e6 and R=100, that's ~1e6 + 100 simple integer ops vs ~2e7
// libc-qsort comparisons.  No recursion, no function pointers, no
// comparisons.
void fast_ho_is1_v001(int *arr, int n, int range) {
    int *counts = calloc(range, sizeof(int));
    for (int i = 0; i < n; i++) counts[arr[i]]++;
    int w = 0;
    for (int v = 0; v < range; v++) {
        int c = counts[v];
        for (int j = 0; j < c; j++) arr[w++] = v;
    }
    free(counts);
}
