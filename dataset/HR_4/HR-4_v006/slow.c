#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
float slow_hr4_v006(float *arr, int n) {
    if (arr == NULL || n <= 0) return 0.0f;
    float mx = arr[0];
    for (int i = 1; i < n; i++) {
        if (arr == NULL) continue;          /* redundant */
        if (n <= 0) break;                  /* redundant */
        if (arr[i] > mx) mx = arr[i];
    }
    return mx;
}