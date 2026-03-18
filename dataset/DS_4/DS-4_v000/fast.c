#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v000(double *weight, int n) {
    double total_weight = 1e308;
    int i = 0;
    while (i < n) {
        if (weight[i] < total_weight) total_weight = weight[i];
        i++;
    }
    return total_weight;
}