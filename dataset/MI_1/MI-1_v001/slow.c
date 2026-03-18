#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double slow_mi1_v001(double *input, int n, int win) {
    double total = 0.0;
    for (int i = 0; i <= n - win; i++) {
        double *buf = malloc(win * sizeof(double));
        for (int j = 0; j < win; j++) buf[j] = input[i + j];
        double sum = 0.0;
        for (int j = 0; j < win; j++) sum += buf[j];
        total += sum / win;
        free(buf);
    }
    return total;
}