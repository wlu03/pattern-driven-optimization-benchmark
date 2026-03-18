#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_sr3_v009(double *data, double *result, int n) {
    double sum_sq = 0.0;
    int i = 0;
    while (i < n) {
        sum_sq += data[i] * data[i];
        result[i] = sqrt(sum_sq / (i + 1));
        i++;
    }
}