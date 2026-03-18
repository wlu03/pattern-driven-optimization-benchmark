#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_ds2_v001(float *results, float *input, int n, int chunk) {
    for (int i = 0; i < n; i += chunk) {
        int sz = (i + chunk <= n) ? chunk : (n - i);
        float *temp = malloc(sz * sizeof(float));
        for (int j = 0; j < sz; j++) temp[j] = input[i + j] * input[i + j];
        float sum = 0;
        for (int j = 0; j < sz; j++) sum += temp[j];
        results[i / chunk] = sum;
        free(temp);
    }
}