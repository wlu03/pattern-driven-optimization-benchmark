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
} AoS_v026;

double slow_ds4_v026(AoS_v026 *arr, int n) {
    double total_pad3 = 0.0;
    for (int i = 0; i < n; i++) {
        total_pad3 += (double)arr[i].pad3;
    }
    return total_pad3;
}