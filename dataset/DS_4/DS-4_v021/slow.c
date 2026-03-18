#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
typedef struct {
    double x;
    double y;
    double z;
    double vx;
    double vy;
    double vz;
    double mass;
    double charge;
    double pad0;
    double pad1;
    double pad2;
    double pad3;
    double pad4;
    double pad5;
    double pad6;
    double pad7;
} AoS_v021;

double slow_ds4_v021(AoS_v021 *arr, int n) {
    double total_pad0 = 0.0;
    for (int i = 0; i < n; i++) {
        total_pad0 += (double)arr[i].pad0;
    }
    return total_pad0;
}