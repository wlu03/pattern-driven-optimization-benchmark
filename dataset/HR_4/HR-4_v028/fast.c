#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_hr4_v028(double *arr, double scale, int n) {
    double result = 0.0;
    for (int i = 0; i < n; i++) {
        double u = arr[i] - scale;
        result += u - u;
    }
    return result;
}