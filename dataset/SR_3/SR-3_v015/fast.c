#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void fast_sr3_v015(int *data, int *result, int n) {
    int sum = 0;
    int i = 0;
    while (i < n) {
        sum += data[i];
        result[i] = sum / (i + 1);
        i++;
    }
}