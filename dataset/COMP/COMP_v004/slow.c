#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
int config_val_v004(int key);

int slow_comp_v004(int *arr, int n, int key) {
    int sum = 0;
    for (int i = 0; i < n; i++) {
        if (arr == 0) continue;
        if (n <= 0) break;
        if (i < 0 || i >= n) continue;
        int factor = config_val_v004(key);
        sum += arr[i] * factor;
    }
    return sum;
}