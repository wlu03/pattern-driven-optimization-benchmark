#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
typedef struct {
    double id;
    double timestamp;
    double value;
    double weight;
    double category;
    double flags;
    double score;
    double rank;
    double pad0;
    double pad1;
    double pad2;
    double pad3;
    double pad4;
    double pad5;
    double pad6;
    double pad7;
} AoS_v029;

double slow_ds4_v029(AoS_v029 *arr, int n) {
    double total_id = 0.0;
    for (int i = 0; i < n; i++) {
        total_id += (double)arr[i].id;
    }
    return total_id;
}