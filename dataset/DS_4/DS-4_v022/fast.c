#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v022(double *pad7, double *pad2, int n) {
    double total_pad7 = 0.0;
    double total_pad2 = 0.0;
    for (int i = 0; i < n; i++) {
        total_pad7 += pad7[i];
        total_pad2 += pad2[i];
    }
    return total_pad7 + total_pad2;
}