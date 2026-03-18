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
} AoS_v008;

double slow_ds4_v008(AoS_v008 *arr, int n) {
    double total_flags = 1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].flags < total_flags) total_flags = (double)arr[i].flags;
    }
    return total_flags;
}