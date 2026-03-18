#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
static int cmp_is4_s_v022(const void *a, const void *b);

void slow_is4_v022(int *arr, int n) {
    qsort(arr, n, sizeof(int), cmp_is4_s_v022);
}
static int cmp_is4_s_v022(const void *a, const void *b) {
    return (*(const int*)a - *(const int*)b);
}