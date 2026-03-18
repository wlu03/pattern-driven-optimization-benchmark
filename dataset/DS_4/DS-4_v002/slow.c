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
} AoS_v002;

double slow_ds4_v002(AoS_v002 *arr, int n) {
    double total_depth = 0.0;
    double total_y = 0.0;
    double total_b = 0.0;
    double total_normal_x = 0.0;
    int i = 0;
    while (i < n) {
        total_depth += (double)arr[i].depth;
        total_y += (double)arr[i].y;
        total_b += (double)arr[i].b;
        total_normal_x += (double)arr[i].normal_x;
        i++;
    }
    return total_depth + total_y + total_b + total_normal_x;
}