#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
int slow_comp_v000(int *X, int *Y, int n, int alpha, int beta) {
    int result = 0;
    for (int i = 0; i < n; i++) {
        int t1 = X[i] * X[i];
        int t2 = alpha * t1;
        int t3 = beta * Y[i];
        int t4 = t2 + t3;
        int t5 = t4 + alpha * beta;
        int t6 = t5;
        result += t6;
    }
    return result;
}