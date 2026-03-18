#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double config_val_v010(int key);

double fast_comp_v010(double *arr, int n, int key) {
    if (arr == 0 || n <= 0) return 0;
    double factor = config_val_v010(key);
    double sum = 0;
    for (int i = 0; i < n; i++) sum += arr[i] * factor;
    return sum;
}