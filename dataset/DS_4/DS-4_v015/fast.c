#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v015(double *pad4, int n) {
    double total_pad4 = -1e308;
    int i = 0;
    while (i < n) {
        if (pad4[i] > total_pad4) total_pad4 = pad4[i];
        i++;
    }
    return total_pad4;
}