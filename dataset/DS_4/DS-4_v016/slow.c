#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
typedef struct {
    double r;
    double g;
    double b;
    double a;
    double x;
    double y;
    double depth;
    double normal_x;
    double pad0;
    double pad1;
    double pad2;
    double pad3;
    double pad4;
    double pad5;
    double pad6;
    double pad7;
} AoS_v016;

double slow_ds4_v016(AoS_v016 *arr, int n) {
    double total_b = 1e308;
    double total_x = 1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].b < total_b) total_b = (double)arr[i].b;
        if ((double)arr[i].x < total_x) total_x = (double)arr[i].x;
    }
    return total_b + total_x;
}