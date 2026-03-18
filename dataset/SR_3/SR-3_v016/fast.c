#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_sr3_v016(double *data, double *result, int n) {
    double sum = 0.0;
    int i = 0;
    while (i < n) {
        sum += data[i];
        result[i] = sum / (i + 1);
        i++;
    }
}