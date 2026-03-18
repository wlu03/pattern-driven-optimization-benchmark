#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
int fast_is3_v000(float *arr, int n, float thresh) {
    for (int i = 0; i < n; i++) {
        if (arr[i] > thresh) return 0;
    }
    return 1;
}