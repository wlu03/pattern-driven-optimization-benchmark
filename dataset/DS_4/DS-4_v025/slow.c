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
} AoS_v025;

double slow_ds4_v025(AoS_v025 *arr, int n) {
    double total_z = 0.0;
    double total_vy = 0.0;
    double total_vz = 0.0;
    int i = 0;
    while (i < n) {
        total_z += (double)arr[i].z;
        total_vy += (double)arr[i].vy;
        total_vz += (double)arr[i].vz;
        i++;
    }
    return total_z + total_vy + total_vz;
}