#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double slow_ds3_v025(const double *data) {
    double *copy = (double*)malloc(512 * sizeof(double));
    for (int i = 0; i < 512; i++) copy[i] = data[i];
    double s = 0.0;
    for (int i = 0; i < 512; i++) s += copy[i];
    free(copy);
    return s / 512.0;
}