#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
typedef struct {
    double px;
    double py;
    double pz;
    double nx;
    double ny;
    double nz;
    double u;
    double v;
    double pad0;
    double pad1;
    double pad2;
    double pad3;
    double pad4;
    double pad5;
    double pad6;
    double pad7;
} AoS_v014;

double slow_ds4_v014(AoS_v014 *arr, int n) {
    double total_pad4 = 0.0;
    for (int i = 0; i < n; i++) {
        total_pad4 += (double)arr[i].pad4;
    }
    return total_pad4;
}