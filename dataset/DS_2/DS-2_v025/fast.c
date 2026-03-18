#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_ds2_v025(double *results, double *input, int n, int chunk) {
    double *temp = malloc(chunk * sizeof(double));
    for (int i = 0; i < n; i += chunk) {
        int sz = (i + chunk <= n) ? chunk : (n - i);
        for (int j = 0; j < sz; j++) temp[j] = input[i + j];
        double sum = 0;
        for (int j = 0; j < sz; j++) sum += temp[j];
        results[i / chunk] = sum;
    }
    free(temp);
}