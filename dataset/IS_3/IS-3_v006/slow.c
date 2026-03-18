#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
int slow_is3_v006(float *arr, int n, float thresh) {
    int count = 0;
    for (int i = 0; i < n; i++) {
        if (arr[i] >= thresh) count++;
    }
    return count == 0;
}