#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
float fast_comp_v014(float *mass, int n) {
    float total = 0;
    for (int i = 0; i < n; i++) total += mass[i];
    return total;
}