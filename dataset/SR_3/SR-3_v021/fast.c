#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_sr3_v021(int *data, int *result, int n) {
    int sum = 0;
    int i = 0;
    while (i < n) {
        sum += data[i];
        if (i >= 16) sum -= data[i - 16];
        int count = (i < 16) ? i + 1 : 16;
        result[i] = sum / count;
        i++;
    }
}