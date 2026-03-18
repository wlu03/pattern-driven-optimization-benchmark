#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_sr3_v002(double *data, double *result, int n) {
    double sum = 0.0;
    for (int i = 0; i < n; i++) {
        sum += data[i];
        if (i >= 64) sum -= data[i - 64];
        int count = (i < 64) ? i + 1 : 64;
        result[i] = sum / count;
    }
}