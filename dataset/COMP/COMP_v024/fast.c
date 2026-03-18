#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
int fast_comp_v024(int *mass, int n) {
    int total = 0;
    for (int i = 0; i < n; i++) total += mass[i];
    return total;
}