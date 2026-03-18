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
} AoS_v010;

double slow_ds4_v010(AoS_v010 *arr, int n) {
    double total_y = 1e308;
    double total_x = 1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].y < total_y) total_y = (double)arr[i].y;
        if ((double)arr[i].x < total_x) total_x = (double)arr[i].x;
    }
    return total_y + total_x;
}