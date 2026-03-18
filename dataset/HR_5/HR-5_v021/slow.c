#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
int hr5_check_v021(int val);
void slow_hr5_v021(int *out, int *A, int *B, int n) {
    int pos = 0;
    for (int i = 0; i < n; i++) {
        int val = A[i] + B[i];
        if (hr5_check_v021(val)) {
            out[pos++] = val;
        }
    }
}