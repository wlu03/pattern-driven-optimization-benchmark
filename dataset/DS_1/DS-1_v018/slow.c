#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
int slow_ds1_v018(int *keys, int *values, int n, int target) {
    for (int i = 0; i < n; i++) {
        if (keys[i] == target) return values[i];
    }
    return -1;
}