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
} AoS_v023;

double slow_ds4_v023(AoS_v023 *arr, int n) {
    double total_charge = -1e308;
    double total_pad6 = -1e308;
    for (int i = 0; i < n; i++) {
        if ((double)arr[i].charge > total_charge) total_charge = (double)arr[i].charge;
        if ((double)arr[i].pad6 > total_pad6) total_pad6 = (double)arr[i].pad6;
    }
    return total_charge + total_pad6;
}