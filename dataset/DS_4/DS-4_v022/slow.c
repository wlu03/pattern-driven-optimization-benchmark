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
} AoS_v022;

double slow_ds4_v022(AoS_v022 *arr, int n) {
    double total_pad7 = 0.0;
    double total_pad2 = 0.0;
    for (int i = 0; i < n; i++) {
        total_pad7 += (double)arr[i].pad7;
        total_pad2 += (double)arr[i].pad2;
    }
    return total_pad7 + total_pad2;
}