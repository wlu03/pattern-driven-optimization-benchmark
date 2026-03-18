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
} AoS_v016;

double slow_ds4_v016(AoS_v016 *arr, int n) {
    double total_id = -1e308;
    int i = 0;
    while (i < n) {
        if ((double)arr[i].id > total_id) total_id = (double)arr[i].id;
        i++;
    }
    return total_id;
}