#include <math.h>
__attribute__((noinline))
void fast_hr1_v005(double *out, double *A, double *B, double *C, double *D, int n) {
    int i = 0;
    while (i < n) {
        out[i] = ((((((double)sqrt(A[i] * A[i] + B[i] * B[i])) - C[i]) + D[i]) + A[i]) + B[i]) + A[i];
        i++;
    }
}