#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
int config_val_v028(int key);

int fast_comp_v028(int *arr, int n, int key) {
    if (arr == 0 || n <= 0) return 0;
    int factor = config_val_v028(key);
    int sum = 0;
    for (int i = 0; i < n; i++) sum += arr[i] * factor;
    return sum;
}