#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_sr3_v019(double *data, double *result, int n) {
    for (int i = 0; i < n; i++) {
        double ema = data[0];
        for (int j = 1; j <= i; j++)
            ema = 0.5 * data[j] + (1.0 - 0.5) * ema;
        result[i] = ema;
    }
}