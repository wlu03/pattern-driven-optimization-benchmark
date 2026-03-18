#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double slow_ds3_v004(const double *data) {
    double *copy = (double*)malloc(64 * sizeof(double));
    for (int i = 0; i < 64; i++) copy[i] = data[i];
    double mx = copy[0];
    for (int i = 1; i < 64; i++) if (copy[i] > mx) mx = copy[i];
    free(copy);
    return mx;
}