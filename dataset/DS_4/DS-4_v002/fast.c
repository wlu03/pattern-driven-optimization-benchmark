#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v002(double *id, int n) {
    double total_id = 0.0;
    for (int i = 0; i < n; i++) {
        total_id += id[i];
    }
    return total_id;
}