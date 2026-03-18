#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
float expensive_fn_v029(int key);

void slow_sr4_v029(float *arr, int n, int key) {
    int i = 0;
    while (i < n) {
        float f0 = expensive_fn_v029(key);
        arr[i] += f0;
        i++;
    }
}
float expensive_fn_v029(int key) {
    unsigned int h = (unsigned int)key;
    float r = 0.0f;
    for (int i = 0; i < 200; i++) {
        h = h * 2654435761u;
        r += (float)(h & 0xFFFF) / 65536.0f;
    }
    return r / 200;
}