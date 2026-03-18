#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double slow_mi3_v010(double *data, int n) {
    double total = 0.0;
    for (int i = 0; i < n - 15; i++) {
        double *quad = malloc(16 * sizeof(double));
        for (int j = 0; j < 16; j++) quad[j] = data[i+j];
        double s = 0.0; for (int j = 0; j < 16; j++) s += quad[j];
        total += s;
        free(quad);
    }
    return total;
}