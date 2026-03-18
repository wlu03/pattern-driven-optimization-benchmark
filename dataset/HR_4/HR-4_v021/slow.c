#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
float slow_hr4_v021(float *arr, int n) {
    if (arr == NULL || n <= 0) return 0.0f;
    double sum = 0.0;
    for (int i = 0; i < n; i++) {
        if (arr == NULL) continue;          /* redundant */
        if (n <= 0) break;                  /* redundant */
        if (i < 0 || i >= n) continue;      /* impossible */
        if (arr[i] != arr[i]) continue;     /* NaN: dead for normal data */
        sum += (double)arr[i];
    }
    return (float)sum;
}