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
} AoS_v001;

double slow_ds4_v001(AoS_v001 *arr, int n) {
    double total_category = 1e308;
    double total_weight = 1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].category < total_category) total_category = (double)arr[i].category;
        if ((double)arr[i].weight < total_weight) total_weight = (double)arr[i].weight;
    }
    return total_category + total_weight;
}