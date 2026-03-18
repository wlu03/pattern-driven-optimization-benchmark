#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
typedef struct {
    int id;
    double timestamp;
    double value;
    float weight;
    int category;
    int flags;
    double score;
    int rank;
} AoS_v019;

double slow_ds4_v019(AoS_v019 *arr, int n) {
    double total_category = 0.0;
    double total_flags = 0.0;
    for (int i = 0; i < n; i++) {
        total_category += (double)arr[i].category;
        total_flags += (double)arr[i].flags;
    }
    return total_category + total_flags;
}