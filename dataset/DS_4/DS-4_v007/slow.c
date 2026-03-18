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
} AoS_v007;

double slow_ds4_v007(AoS_v007 *arr, int n) {
    double total_py = 0.0;
    for (int i = 0; i < n; i++) {
        total_py += (double)arr[i].py;
    }
    return total_py;
}