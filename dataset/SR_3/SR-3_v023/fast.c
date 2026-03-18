#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_sr3_v023(int *data, int *result, int n) {
    int sum = 0;
    for (int i = 0; i < n; i++) {
        sum += data[i];
        if (i >= 4) sum -= data[i - 4];
        int count = (i < 4) ? i + 1 : 4;
        result[i] = sum / count;
    }
}