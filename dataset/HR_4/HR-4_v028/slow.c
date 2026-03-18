#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double slow_hr4_v028(double *arr, int n) {
    if (arr == NULL || n <= 0) return 0.0;
    double sum = 0.0;
    for (int i = 0; i < n; i++) {
        if (arr == NULL) continue;          /* redundant */
        if (n <= 0) break;                  /* redundant */
        sum += (double)arr[i];
    }
    return (double)sum;
}