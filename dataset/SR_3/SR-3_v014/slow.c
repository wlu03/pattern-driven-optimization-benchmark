#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_sr3_v014(float *data, float *result, int n) {
    for (int i = 0; i < n; i++) {
        float sum = 0.0f;
        for (int j = 0; j <= i; j++) sum += data[j];
        float mean = sum / (i + 1);
        float var_sum = 0.0f;
        for (int j = 0; j <= i; j++) {
            float diff = data[j] - mean;
            var_sum += diff * diff;
        }
        result[i] = var_sum / (i + 1);
    }
}