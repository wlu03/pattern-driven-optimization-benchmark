#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v016(double *id, int n) {
    double total_id = -1e308;
    int i = 0;
    while (i < n) {
        if (id[i] > total_id) total_id = id[i];
        i++;
    }
    return total_id;
}