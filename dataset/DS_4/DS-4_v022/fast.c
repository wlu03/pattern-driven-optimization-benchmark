#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v022(double *light, int n) {
    double total_light = 1e308;
    for (int i = 0; i < n; i++) {
        if (light[i] < total_light) total_light = light[i];
    }
    return total_light;
}