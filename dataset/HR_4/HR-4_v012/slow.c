#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double slow_hr4_v012(double *arr, double scale, int n) {
    double *t1 = (double *)malloc(n * sizeof(double));
    double *t2 = (double *)malloc(n * sizeof(double));
    for (int i = 0; i < n; i++) t1[i] = arr[i] - scale;
    for (int i = 0; i < n; i++) t2[i] = t1[i] + t1[i];
    double result = 0.0;
    for (int i = 0; i < n; i++) result += t2[i];
    free(t1);
    free(t2);
    return result;
}