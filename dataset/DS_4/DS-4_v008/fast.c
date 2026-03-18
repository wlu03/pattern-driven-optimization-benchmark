#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v008(double *flags, int n) {
    double total_flags = 1e308;
    for (int i = 0; i < n; i++) {
        if (flags[i] < total_flags) total_flags = flags[i];
    }
    return total_flags;
}