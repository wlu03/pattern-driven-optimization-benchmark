#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v023(double *category, double *id, double *score, double *value, int n) {
    double total_category = 0.0;
    double total_id = 0.0;
    double total_score = 0.0;
    double total_value = 0.0;
    for (int i = 0; i < n; i++) {
        total_category += category[i];
        total_id += id[i];
        total_score += score[i];
        total_value += value[i];
    }
    return total_category + total_id + total_score + total_value;
}