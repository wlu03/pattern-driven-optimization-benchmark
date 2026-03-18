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
} AoS_v007;

double slow_ds4_v007(AoS_v007 *arr, int n) {
    double total_g = 1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].g < total_g) total_g = (double)arr[i].g;
    }
    return total_g;
}