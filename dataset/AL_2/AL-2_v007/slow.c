#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
static int cmp_al2_v007(const void *a, const void *b);

void slow_al2_v007(double *arr, int *sz, double *items, int n) {
    *sz = 0;
    for (int i = 0; i < n; i++) {
        arr[(*sz)++] = items[i];
        qsort(arr, *sz, sizeof(double), cmp_al2_v007);
    }
}
static int cmp_al2_v007(const void *a, const void *b) {
    double da = *(const double*)a, db = *(const double*)b;
    return (da > db) - (da < db);
}