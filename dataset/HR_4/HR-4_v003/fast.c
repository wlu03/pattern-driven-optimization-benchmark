#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
float fast_hr4_v003(float *arr, int n) {
    if (arr == NULL || n <= 0) return 0.0f;
    float mx = arr[0];
    for (int i = 1; i < n; i++) if (arr[i] > mx) mx = arr[i];
    return mx;
}