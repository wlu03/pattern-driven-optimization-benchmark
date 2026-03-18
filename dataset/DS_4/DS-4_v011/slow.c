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
} AoS_v011;

double slow_ds4_v011(AoS_v011 *arr, int n) {
    double total_vx = 0.0;
    double total_x = 0.0;
    double total_vy = 0.0;
    double total_y = 0.0;
    int i = 0;
    while (i < n) {
        total_vx += (double)arr[i].vx;
        total_x += (double)arr[i].x;
        total_vy += (double)arr[i].vy;
        total_y += (double)arr[i].y;
        i++;
    }
    return total_vx + total_x + total_vy + total_y;
}