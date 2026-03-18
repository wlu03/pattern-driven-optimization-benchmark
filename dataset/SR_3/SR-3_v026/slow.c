#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_sr3_v026(float *data, float *result, int n) {
    for (int i = 0; i < n; i++) {
        float sum = 0.0f;
        int start = (i >= 8) ? i - 8 + 1 : 0;
        for (int j = start; j <= i; j++) sum += data[j];
        result[i] = sum;
    }
}