#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_sr3_v015(int *data, int *result, int n) {
    int sum = 0;
    for (int i = 0; i < n; i++) {
        sum += data[i];
        if (i >= 32) sum -= data[i - 32];
        result[i] = sum;
    }
}