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
} AoS_v026;

double slow_ds4_v026(AoS_v026 *arr, int n) {
    double total_depth = 0.0;
    double total_x = 0.0;
    double total_y = 0.0;
    double total_g = 0.0;
    for (int i = 0; i < n; i++) {
        total_depth += (double)arr[i].depth;
        total_x += (double)arr[i].x;
        total_y += (double)arr[i].y;
        total_g += (double)arr[i].g;
    }
    return total_depth + total_x + total_y + total_g;
}