#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_sr3_v012(int *data, int *result, int n) {
    int sum = 0;
    int i = 0;
    while (i < n) {
        sum += data[i];
        if (i >= 64) sum -= data[i - 64];
        int count = (i < 64) ? i + 1 : 64;
        result[i] = sum / count;
        i++;
    }
}