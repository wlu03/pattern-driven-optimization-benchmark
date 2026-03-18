#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_mi1_v029(double *input, int n, int win) {
    double total = 0.0, sum = 0.0;
    for (int j = 0; j < win; j++) sum += input[j];
    total += sum / win;
    for (int i = 1; i <= n - win; i++) {
        sum += input[i + win - 1] - input[i - 1];
        total += sum / win;
    }
    return total;
}