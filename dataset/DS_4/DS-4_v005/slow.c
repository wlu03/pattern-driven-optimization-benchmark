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
} AoS_v005;

double slow_ds4_v005(AoS_v005 *arr, int n) {
    double total_g = 0.0;
    double total_r = 0.0;
    double total_b = 0.0;
    double total_a = 0.0;
    for (int i = 0; i < n; i++) {
        total_g += (double)arr[i].g;
        total_r += (double)arr[i].r;
        total_b += (double)arr[i].b;
        total_a += (double)arr[i].a;
    }
    return total_g + total_r + total_b + total_a;
}