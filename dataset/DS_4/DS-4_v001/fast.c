#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v001(double *flags, int n) {
    double total_flags = 1e308;
    int i = 0;
    while (i < n) {
        if (flags[i] < total_flags) total_flags = flags[i];
        i++;
    }
    return total_flags;
}