#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_sr3_v024(float *data, float *result, int n) {
    for (int i = 0; i < n; i++) {
        float ema = data[0];
        for (int j = 1; j <= i; j++)
            ema = 0.2f * data[j] + (1.0f - 0.2f) * ema;
        result[i] = ema;
    }
}