#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_sr3_v024(float *data, float *result, int n) {
    result[0] = data[0];
    for (int i = 1; i < n; i++) {
        result[i] = 0.2f * data[i] + (1.0f - 0.2f) * result[i-1];
    }
}