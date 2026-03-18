#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
static int cmp_is4_f_v023(const void *a, const void *b);

void fast_is4_v023(int *arr, int n) {
    int inv = 0;
    unsigned s = 12345u;
    for (int k = 0; k < 64; k++) {
        s = s * 1664525u + 1013904223u;
        int i = (int)((s >> 1) % (unsigned)(n - 1));
        if (arr[i] > arr[i + 1]) inv++;
    }
    if (inv <= 2) {
        for (int i = 1; i < n; i++) {
            int key = arr[i], j = i - 1;
            while (j >= 0 && arr[j] > key) { arr[j + 1] = arr[j]; j--; }
            arr[j + 1] = key;
        }
    } else {
        qsort(arr, n, sizeof(int), cmp_is4_f_v023);
    }
}
static int cmp_is4_f_v023(const void *a, const void *b) {
    return (*(const int*)a - *(const int*)b);
}