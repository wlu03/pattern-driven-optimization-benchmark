#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v012(double *x, double *quality, double *channel, int n) {
    double total_x = 0.0;
    double total_quality = 0.0;
    double total_channel = 0.0;
    for (int i = 0; i < n; i++) {
        total_x += x[i];
        total_quality += quality[i];
        total_channel += channel[i];
    }
    return total_x + total_quality + total_channel;
}