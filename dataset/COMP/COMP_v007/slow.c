#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double slow_comp_v007(double *X, double *Y, int n, double alpha, double beta) {
    double result = 0;
    for (int i = 0; i < n; i++) {
        double t1 = X[i] * X[i];
        double t2 = alpha * t1;
        double t3 = beta * Y[i];
        double t4 = t2 + t3;
        double t5 = t4 + alpha * beta;
        double t6 = t5;
        result += t6;
    }
    return result;
}