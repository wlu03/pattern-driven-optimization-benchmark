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
} AoS_v008;

double slow_ds4_v008(AoS_v008 *arr, int n) {
    double total_depth = 0.0;
    double total_r = 0.0;
    double total_g = 0.0;
    double total_b = 0.0;
    for (int i = 0; i < n; i++) {
        total_depth += (double)arr[i].depth;
        total_r += (double)arr[i].r;
        total_g += (double)arr[i].g;
        total_b += (double)arr[i].b;
    }
    return total_depth + total_r + total_g + total_b;
}