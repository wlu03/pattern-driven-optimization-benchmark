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
} AoS_v027;

double slow_ds4_v027(AoS_v027 *arr, int n) {
    double total_weight = 1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].weight < total_weight) total_weight = (double)arr[i].weight;
    }
    return total_weight;
}