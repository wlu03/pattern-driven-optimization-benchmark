#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
static int cmp_is4_s_v015(const void *a, const void *b);

void slow_is4_v015(int *arr, int n) {
    qsort(arr, n, sizeof(int), cmp_is4_s_v015);
}
static int cmp_is4_s_v015(const void *a, const void *b) {
    return (*(const int*)a - *(const int*)b);
}