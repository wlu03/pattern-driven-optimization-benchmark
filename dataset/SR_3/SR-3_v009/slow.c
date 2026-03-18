#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_sr3_v009(double *data, double *result, int n) {
    for (int i = 0; i < n; i++) {
        double sum_sq = 0.0;
        for (int j = 0; j <= i; j++) sum_sq += data[j] * data[j];
        result[i] = sqrt(sum_sq / (i + 1));
    }
}