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
} AoS_v005;

double slow_ds4_v005(AoS_v005 *arr, int n) {
    double total_y = 0.0;
    double total_depth = 0.0;
    double total_a = 0.0;
    for (int i = 0; i < n; i++) {
        total_y += (double)arr[i].y;
        total_depth += (double)arr[i].depth;
        total_a += (double)arr[i].a;
    }
    return total_y + total_depth + total_a;
}