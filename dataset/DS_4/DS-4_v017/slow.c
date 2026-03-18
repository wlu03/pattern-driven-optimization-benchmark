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
} AoS_v017;

double slow_ds4_v017(AoS_v017 *arr, int n) {
    double total_vx = 0.0;
    double total_charge = 0.0;
    double total_vz = 0.0;
    for (int i = 0; i < n; i++) {
        total_vx += (double)arr[i].vx;
        total_charge += (double)arr[i].charge;
        total_vz += (double)arr[i].vz;
    }
    return total_vx + total_charge + total_vz;
}