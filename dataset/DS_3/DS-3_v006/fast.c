#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds3_v006(const double *data) {
    double mx = data[0];
    for (int i = 1; i < 128; i++) if (data[i] > mx) mx = data[i];
    return mx;
}