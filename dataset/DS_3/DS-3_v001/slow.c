#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double slow_ds3_v001(const double *data) {
    double *copy = (double*)malloc(512 * sizeof(double));
    for (int i = 0; i < 512; i++) copy[i] = data[i];
    double mx = copy[0];
    for (int i = 1; i < 512; i++) if (copy[i] > mx) mx = copy[i];
    free(copy);
    return mx;
}