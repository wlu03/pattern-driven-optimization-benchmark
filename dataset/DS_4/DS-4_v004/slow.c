#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
typedef struct {
    int r;
    int g;
    int b;
    int a;
    int x;
    int y;
    float depth;
} AoS_v004;

double slow_ds4_v004(AoS_v004 *arr, int n) {
    double total_y = 1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].y < total_y) total_y = (double)arr[i].y;
    }
    return total_y;
}