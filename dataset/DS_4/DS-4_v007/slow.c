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
} AoS_v007;

double slow_ds4_v007(AoS_v007 *arr, int n) {
    double total_vy = 0.0;
    for (int i = 0; i < n; i++) {
        total_vy += (double)arr[i].vy;
    }
    return total_vy;
}