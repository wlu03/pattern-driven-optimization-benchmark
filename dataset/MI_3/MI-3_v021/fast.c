#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
float fast_mi3_v021(float *data, int n) {
    float total = 0.0f;
    for (int i = 0; i < n - 3; i++) {
        total += data[i+0] + data[i+1] + data[i+2] + data[i+3];
    }
    return total;
}