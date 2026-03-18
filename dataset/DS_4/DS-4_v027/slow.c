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
} AoS_v027;

double slow_ds4_v027(AoS_v027 *arr, int n) {
    double total_pad7 = -1e308;
    double total_pad6 = -1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].pad7 > total_pad7) total_pad7 = (double)arr[i].pad7;
        if ((double)arr[i].pad6 > total_pad6) total_pad6 = (double)arr[i].pad6;
    }
    return total_pad7 + total_pad6;
}