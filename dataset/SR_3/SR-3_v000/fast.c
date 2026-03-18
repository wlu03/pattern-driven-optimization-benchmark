#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_sr3_v000(double *data, double *result, int n) {
    double sum = 0.0;
    int i = 0;
    while (i < n) {
        sum += data[i];
        if (i >= 128) sum -= data[i - 128];
        int count = (i < 128) ? i + 1 : 128;
        result[i] = sum / count;
        i++;
    }
}