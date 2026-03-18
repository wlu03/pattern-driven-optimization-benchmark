#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_sr3_v018(float *data, float *result, int n) {
    float sum = 0.0f;
    for (int i = 0; i < n; i++) {
        sum += data[i];
        if (i >= 16) sum -= data[i - 16];
        int count = (i < 16) ? i + 1 : 16;
        result[i] = sum / count;
    }
}