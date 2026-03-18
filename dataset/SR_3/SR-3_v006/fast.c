#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_sr3_v006(int *data, int *result, int n) {
    int sum = 0;
    int i = 0;
    while (i < n) {
        sum += data[i];
        if (i >= 8) sum -= data[i - 8];
        int count = (i < 8) ? i + 1 : 8;
        result[i] = sum / count;
        i++;
    }
}