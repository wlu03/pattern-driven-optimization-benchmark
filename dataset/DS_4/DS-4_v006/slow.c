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
} AoS_v006;

double slow_ds4_v006(AoS_v006 *arr, int n) {
    double total_vx = 0.0;
    double total_z = 0.0;
    double total_mass = 0.0;
    int i = 0;
    while (i < n) {
        total_vx += (double)arr[i].vx;
        total_z += (double)arr[i].z;
        total_mass += (double)arr[i].mass;
        i++;
    }
    return total_vx + total_z + total_mass;
}