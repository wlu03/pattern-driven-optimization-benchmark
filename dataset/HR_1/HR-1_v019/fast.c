#include <math.h>
__attribute__((noinline))
void fast_hr1_v019(int *out, int *A, int *B, int n) {
    for (int i = 0; i < n; i++) {
        out[i] = ((((int)sqrt(A[i] * A[i] + B[i] * B[i])) - A[i]) + B[i]) - A[i];
    }
}