#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v014(double *weight, double *value, double *category, int n) {
    double total_weight = 0.0;
    double total_value = 0.0;
    double total_category = 0.0;
    for (int i = 0; i < n; i++) {
        total_weight += weight[i];
        total_value += value[i];
        total_category += category[i];
    }
    return total_weight + total_value + total_category;
}