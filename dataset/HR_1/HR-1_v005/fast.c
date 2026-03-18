#include <math.h>
__attribute__((noinline))
void fast_hr1_v005(double *out, double *A, double *B, double *C, int n) {
    for (int i = 0; i < n; i++) {
        out[i] = (((((double)sqrt(A[i] * A[i] + B[i] * B[i])) * C[i]) * A[i]) * B[i]) - A[i];
    }
}