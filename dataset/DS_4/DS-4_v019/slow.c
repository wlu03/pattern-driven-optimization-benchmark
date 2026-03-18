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
    float normal_x;
} AoS_v019;

double slow_ds4_v019(AoS_v019 *arr, int n) {
    double total_r = 0.0;
    double total_x = 0.0;
    double total_normal_x = 0.0;
    double total_a = 0.0;
    for (int i = 0; i < n; i++) {
        total_r += (double)arr[i].r;
        total_x += (double)arr[i].x;
        total_normal_x += (double)arr[i].normal_x;
        total_a += (double)arr[i].a;
    }
    return total_r + total_x + total_normal_x + total_a;
}