#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_sr3_v025(double *data, double *result, int n) {
    double mx = data[0];
    result[0] = mx;
    for (int i = 1; i < n; i++) {
        if (data[i] > mx) mx = data[i];
        result[i] = mx;
    }
}