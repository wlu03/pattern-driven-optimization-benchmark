#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds3_v017(const double *data) {
    double mx = data[0];
    for (int i = 1; i < 64; i++) if (data[i] > mx) mx = data[i];
    return mx;
}