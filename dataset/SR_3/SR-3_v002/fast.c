#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_sr3_v002(double *data, double *result, int n) {
    double mean = 0.0;
    double M2 = 0.0;
    int i = 0;
    while (i < n) {
        double delta = data[i] - mean;
        mean += delta / (i + 1);
        double delta2 = data[i] - mean;
        M2 += delta * delta2;
        result[i] = M2 / (i + 1);
        i++;
    }
}