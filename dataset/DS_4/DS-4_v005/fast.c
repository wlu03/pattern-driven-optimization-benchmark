#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v005(double *light, double *noise, int n) {
    double total_light = 0.0;
    double total_noise = 0.0;
    for (int i = 0; i < n; i++) {
        total_light += light[i];
        total_noise += noise[i];
    }
    return total_light + total_noise;
}