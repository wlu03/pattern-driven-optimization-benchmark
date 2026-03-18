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
} AoS_v018;

double slow_ds4_v018(AoS_v018 *arr, int n) {
    double total_r = -1e308;
    double total_depth = -1e308;
    double total_normal_x = -1e308;
    double total_a = -1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].r > total_r) total_r = (double)arr[i].r;
        if ((double)arr[i].depth > total_depth) total_depth = (double)arr[i].depth;
        if ((double)arr[i].normal_x > total_normal_x) total_normal_x = (double)arr[i].normal_x;
        if ((double)arr[i].a > total_a) total_a = (double)arr[i].a;
    }
    return total_r + total_depth + total_normal_x + total_a;
}