#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_sr3_v016(int *data, int *result, int n) {
    int mn = data[0];
    result[0] = mn;
    for (int i = 1; i < n; i++) {
        if (data[i] < mn) mn = data[i];
        result[i] = mn;
    }
}