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
} AoS_v023;

double slow_ds4_v023(AoS_v023 *arr, int n) {
    double total_g = 1e308;
    double total_y = 1e308;
    double total_b = 1e308;
    double total_x = 1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].g < total_g) total_g = (double)arr[i].g;
        if ((double)arr[i].y < total_y) total_y = (double)arr[i].y;
        if ((double)arr[i].b < total_b) total_b = (double)arr[i].b;
        if ((double)arr[i].x < total_x) total_x = (double)arr[i].x;
    }
    return total_g + total_y + total_b + total_x;
}