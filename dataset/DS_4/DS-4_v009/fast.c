#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v009(double *pad6, int n) {
    double total_pad6 = -1e308;
    for (int i = 0; i < n; i++) {
        if (pad6[i] > total_pad6) total_pad6 = pad6[i];
    }
    return total_pad6;
}