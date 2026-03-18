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
} AoS_v010;

double slow_ds4_v010(AoS_v010 *arr, int n) {
    double total_v = -1e308;
    double total_pad2 = -1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].v > total_v) total_v = (double)arr[i].v;
        if ((double)arr[i].pad2 > total_pad2) total_pad2 = (double)arr[i].pad2;
    }
    return total_v + total_pad2;
}