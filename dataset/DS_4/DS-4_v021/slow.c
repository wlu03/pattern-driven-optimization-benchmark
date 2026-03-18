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
} AoS_v021;

double slow_ds4_v021(AoS_v021 *arr, int n) {
    double total_rank = 0.0;
    double total_category = 0.0;
    double total_weight = 0.0;
    double total_id = 0.0;
    int i = 0;
    while (i < n) {
        total_rank += (double)arr[i].rank;
        total_category += (double)arr[i].category;
        total_weight += (double)arr[i].weight;
        total_id += (double)arr[i].id;
        i++;
    }
    return total_rank + total_category + total_weight + total_id;
}