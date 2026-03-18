#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
float config_val_v014(int key);

float fast_comp_v014(float *arr, int n, int key) {
    if (arr == 0 || n <= 0) return 0;
    float factor = config_val_v014(key);
    float sum = 0;
    for (int i = 0; i < n; i++) sum += arr[i] * factor;
    return sum;
}