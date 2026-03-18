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
} AoS_v001;

double slow_ds4_v001(AoS_v001 *arr, int n) {
    double total_flags = 1e308;
    int i = 0;
    while (i < n) {
        if ((double)arr[i].flags < total_flags) total_flags = (double)arr[i].flags;
        i++;
    }
    return total_flags;
}