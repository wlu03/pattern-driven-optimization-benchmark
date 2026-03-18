#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_mi2_v006(double *out, double *A, double *B, int n) {
    double *s1 = (double *)malloc(n * sizeof(double));
    double *s2 = (double *)malloc(n * sizeof(double));
    for (int i = 0; i < n; i++) s1[i] = A[i] * A[i] + B[i];
    for (int i = 0; i < n; i++) s2[i] = s1[i] * s1[i] - B[i];
    for (int i = 0; i < n; i++) out[i] = s2[i];
    free(s1);
    free(s2);
}