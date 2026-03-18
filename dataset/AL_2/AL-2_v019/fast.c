#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
static int bs_insert_v019(double *arr, int sz, double val);

void fast_al2_v019(double *arr, int *sz, double *items, int n) {
    *sz = 0;
    for (int i = 0; i < n; i++) {
        int pos = bs_insert_v019(arr, *sz, items[i]);
        memmove(&arr[pos+1], &arr[pos], (*sz - pos) * sizeof(double));
        arr[pos] = items[i];
        (*sz)++;
    }
}
static int bs_insert_v019(double *arr, int sz, double val) {
    int lo = 0, hi = sz;
    while (lo < hi) { int mid = (lo+hi)/2; if (arr[mid] < val) lo=mid+1; else hi=mid; }
    return lo;
}