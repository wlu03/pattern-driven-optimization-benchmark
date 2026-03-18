#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v027(double *pad7, double *pad6, int n) {
    double total_pad7 = -1e308;
    double total_pad6 = -1e308;
    for (int i = 0; i < n; i++) {
        if (pad7[i] > total_pad7) total_pad7 = pad7[i];
        if (pad6[i] > total_pad6) total_pad6 = pad6[i];
    }
    return total_pad7 + total_pad6;
}