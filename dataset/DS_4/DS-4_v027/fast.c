#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v027(double *weight, int n) {
    double total_weight = 1e308;
    for (int i = 0; i < n; i++) {
        if (weight[i] < total_weight) total_weight = weight[i];
    }
    return total_weight;
}