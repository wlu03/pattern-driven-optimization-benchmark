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
} AoS_v004;

double slow_ds4_v004(AoS_v004 *arr, int n) {
    double total_r = 0.0;
    double total_a = 0.0;
    int i = 0;
    while (i < n) {
        total_r += (double)arr[i].r;
        total_a += (double)arr[i].a;
        i++;
    }
    return total_r + total_a;
}