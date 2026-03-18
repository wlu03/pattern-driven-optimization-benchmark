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
} AoS_v014;

double slow_ds4_v014(AoS_v014 *arr, int n) {
    double total_weight = 0.0;
    double total_value = 0.0;
    double total_category = 0.0;
    for (int i = 0; i < n; i++) {
        total_weight += (double)arr[i].weight;
        total_value += (double)arr[i].value;
        total_category += (double)arr[i].category;
    }
    return total_weight + total_value + total_category;
}