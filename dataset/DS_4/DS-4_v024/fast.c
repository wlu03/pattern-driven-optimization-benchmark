#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v024(double *humidity, double *noise, int n) {
    double total_humidity = 0.0;
    double total_noise = 0.0;
    int i = 0;
    while (i < n) {
        total_humidity += humidity[i];
        total_noise += noise[i];
        i++;
    }
    return total_humidity + total_noise;
}