#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double config_val_v014(int key);

double slow_comp_v014(double *arr, int n, int key) {
    double sum = 0;
    for (int i = 0; i < n; i++) {
        if (arr == 0) continue;
        if (n <= 0) break;
        if (i < 0 || i >= n) continue;
        double factor = config_val_v014(key);
        sum += arr[i] * factor;
    }
    return sum;
}