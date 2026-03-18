#include <math.h>
__attribute__((noinline))
void slow_hr1_v008(double *out, double *A, double *B, double *C, double *D, int n) {
    int i = 0;
    while (i < n) {
        double temp1 = (double)sqrt(A[i] * A[i] + B[i] * B[i]);
        double temp2 = temp1 - C[i];
        double temp3 = temp2 + A[i];
        double result = temp3;
        out[i] = result;
        i++;
    }
}