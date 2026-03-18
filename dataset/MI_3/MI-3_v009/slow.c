#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
float slow_mi3_v009(float *data, int n) {
    float total = 0.0f;
    for (int i = 0; i < n - 7; i++) {
        float *quad = malloc(8 * sizeof(float));
        for (int j = 0; j < 8; j++) quad[j] = data[i+j];
        float s = 0.0f; for (int j = 0; j < 8; j++) s += quad[j];
        total += s * (float)0.125;
        free(quad);
    }
    return total;
}