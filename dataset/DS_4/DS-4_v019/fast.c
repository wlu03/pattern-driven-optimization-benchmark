#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v019(double *category, double *flags, int n) {
    double total_category = 0.0;
    double total_flags = 0.0;
    for (int i = 0; i < n; i++) {
        total_category += category[i];
        total_flags += flags[i];
    }
    return total_category + total_flags;
}