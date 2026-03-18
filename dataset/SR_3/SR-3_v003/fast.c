#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_sr3_v003(float *data, float *result, int n) {
    float mean = 0.0f;
    float M2 = 0.0f;
    int i = 0;
    while (i < n) {
        float delta = data[i] - mean;
        mean += delta / (i + 1);
        float delta2 = data[i] - mean;
        M2 += delta * delta2;
        result[i] = M2 / (i + 1);
        i++;
    }
}