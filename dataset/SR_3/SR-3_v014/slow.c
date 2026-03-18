#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_sr3_v014(int *data, int *result, int n) {
    for (int i = 0; i < n; i++) {
        int sum = 0;
        int start = (i >= 16) ? i - 16 + 1 : 0;
        int count = i - start + 1;
        for (int j = start; j <= i; j++) sum += data[j];
        result[i] = sum / count;
    }
}