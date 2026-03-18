#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
double fast_ds4_v028(double *py, double *nx, int n) {
    double total_py = -1e308;
    double total_nx = -1e308;
    for (int i = 0; i < n; i++) {
        if (py[i] > total_py) total_py = py[i];
        if (nx[i] > total_nx) total_nx = nx[i];
    }
    return total_py + total_nx;
}