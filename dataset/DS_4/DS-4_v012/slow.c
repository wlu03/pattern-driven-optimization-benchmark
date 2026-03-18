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
} AoS_v012;

double slow_ds4_v012(AoS_v012 *arr, int n) {
    double total_normal_x = 0.0;
    double total_depth = 0.0;
    double total_g = 0.0;
    double total_a = 0.0;
    int i = 0;
    while (i < n) {
        total_normal_x += (double)arr[i].normal_x;
        total_depth += (double)arr[i].depth;
        total_g += (double)arr[i].g;
        total_a += (double)arr[i].a;
        i++;
    }
    return total_normal_x + total_depth + total_g + total_a;
}