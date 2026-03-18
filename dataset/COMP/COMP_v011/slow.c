#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
float config_val_v011(int key);

float slow_comp_v011(float *arr, int n, int key) {
    float sum = 0;
    for (int i = 0; i < n; i++) {
        if (arr == 0) continue;
        if (n <= 0) break;
        if (i < 0 || i >= n) continue;
        float factor = config_val_v011(key);
        sum += arr[i] * factor;
    }
    return sum;
}