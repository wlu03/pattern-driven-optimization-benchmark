#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_sr3_v003(int *data, int *result, int n) {
    int sum = 0;
    for (int i = 0; i < n; i++) {
        sum += data[i];
        if (i >= 128) sum -= data[i - 128];
        int count = (i < 128) ? i + 1 : 128;
        result[i] = sum / count;
    }
}