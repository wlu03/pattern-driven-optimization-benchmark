#include <math.h>
__attribute__((noinline))
void fast_hr1_v023(double *out, double *A, double *B, int n) {
    int i = 0;
    while (i < n) {
        out[i] = (((((double)sqrt(A[i] * A[i] + B[i] * B[i])) * A[i]) + B[i]) - A[i]) + A[i];
        i++;
    }
}