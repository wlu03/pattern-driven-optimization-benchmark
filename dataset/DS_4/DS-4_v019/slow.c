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
} AoS_v019;

double slow_ds4_v019(AoS_v019 *arr, int n) {
    double total_py = 1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].py < total_py) total_py = (double)arr[i].py;
    }
    return total_py;
}