#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_sr3_v027(double *data, double *result, int n) {
    result[0] = data[0];
    int i = 1;
    while (i < n) {
        result[i] = 0.2 * data[i] + (1.0 - 0.2) * result[i-1];
        i++;
    }
}