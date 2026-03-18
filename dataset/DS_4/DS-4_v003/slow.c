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
} AoS_v003;

double slow_ds4_v003(AoS_v003 *arr, int n) {
    double total_x = 0.0;
    for (int i = 0; i < n; i++) {
        total_x += (double)arr[i].x;
    }
    return total_x;
}