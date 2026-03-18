#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
typedef struct {
    int r;
    int g;
    int b;
    int a;
    int x;
    int y;
    float depth;
    float normal_x;
} AoS_v015;

double slow_ds4_v015(AoS_v015 *arr, int n) {
    double total_g = 1e308;
    int i = 0;
    while (i < n) {
        if ((double)arr[i].g < total_g) total_g = (double)arr[i].g;
        i++;
    }
    return total_g;
}