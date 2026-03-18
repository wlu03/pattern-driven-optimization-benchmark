#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void slow_hr5_v019(int *out, int *A, int *B, int n) {
    int pos = 0;
    for (int i = 0; i < n; i++) {
        int val = A[i] - B[i];
    if (pos < n) {
        if (val >= 0) {
                    out[pos] = val;
                    pos++;
        } 
    } 
    }
}