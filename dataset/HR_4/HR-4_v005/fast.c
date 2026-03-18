#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
float fast_hr4_v005(float *arr, int n) {
    if (arr == NULL || n <= 0) return 0.0f;
    double sum = 0.0;
    for (int i = 0; i < n; i++) sum += (double)arr[i];
    return (float)sum;
}