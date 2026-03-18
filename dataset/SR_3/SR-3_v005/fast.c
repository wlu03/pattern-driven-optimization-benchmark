#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_sr3_v005(float *data, float *result, int n) {
    float sum = 0.0f;
    int i = 0;
    while (i < n) {
        sum += data[i];
        result[i] = sum / (i + 1);
        i++;
    }
}