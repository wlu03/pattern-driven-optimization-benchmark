#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_ds2_v012(double *results, double *input, int n, int chunk) {
    for (int i = 0; i < n; i += chunk) {
        int sz = (i + chunk <= n) ? chunk : (n - i);
        double *temp = malloc(sz * sizeof(double));
        for (int j = 0; j < sz; j++) temp[j] = (double)fabs((double)input[i + j]);
        double sum = 0;
        for (int j = 0; j < sz; j++) sum += temp[j];
        results[i / chunk] = sum;
        free(temp);
    }
}