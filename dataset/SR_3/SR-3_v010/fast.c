#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_sr3_v010(float *data, float *result, int n) {
    float sum = 0.0f;
    for (int i = 0; i < n; i++) {
        sum += data[i];
        if (i >= 8) sum -= data[i - 8];
        int count = (i < 8) ? i + 1 : 8;
        result[i] = sum / count;
    }
}