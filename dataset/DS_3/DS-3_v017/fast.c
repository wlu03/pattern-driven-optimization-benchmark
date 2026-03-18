#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds3_v017(const double *data) {
    double s = 0.0;
    for (int i = 0; i < 128; i++) s += data[i];
    return s / 128.0;
}