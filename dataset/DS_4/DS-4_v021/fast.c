#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v021(double *rank, double *category, double *weight, double *id, int n) {
    double total_rank = 0.0;
    double total_category = 0.0;
    double total_weight = 0.0;
    double total_id = 0.0;
    int i = 0;
    while (i < n) {
        total_rank += rank[i];
        total_category += category[i];
        total_weight += weight[i];
        total_id += id[i];
        i++;
    }
    return total_rank + total_category + total_weight + total_id;
}