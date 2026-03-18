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
} AoS_v000;

double slow_ds4_v000(AoS_v000 *arr, int n) {
    double total_weight = 1e308;
    int i = 0;
    while (i < n) {
        if ((double)arr[i].weight < total_weight) total_weight = (double)arr[i].weight;
        i++;
    }
    return total_weight;
}