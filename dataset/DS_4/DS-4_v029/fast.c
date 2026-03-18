#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v029(double *id, double *rank, double *flags, double *category, int n) {
    double total_id = -1e308;
    double total_rank = -1e308;
    double total_flags = -1e308;
    double total_category = -1e308;
    for (int i = 0; i < n; i++) {
        if (id[i] > total_id) total_id = id[i];
        if (rank[i] > total_rank) total_rank = rank[i];
        if (flags[i] > total_flags) total_flags = flags[i];
        if (category[i] > total_category) total_category = category[i];
    }
    return total_id + total_rank + total_flags + total_category;
}