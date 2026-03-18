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
} AoS_v023;

double slow_ds4_v023(AoS_v023 *arr, int n) {
    double total_category = 0.0;
    double total_id = 0.0;
    double total_score = 0.0;
    double total_value = 0.0;
    for (int i = 0; i < n; i++) {
        total_category += (double)arr[i].category;
        total_id += (double)arr[i].id;
        total_score += (double)arr[i].score;
        total_value += (double)arr[i].value;
    }
    return total_category + total_id + total_score + total_value;
}