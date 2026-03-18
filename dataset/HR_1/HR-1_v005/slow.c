#include <math.h>
__attribute__((noinline))
void slow_hr1_v005(double *out, double *A, double *B, double *C, double *D, int n) {
    int i = 0;
    while (i < n) {
        double temp1 = (double)sqrt(A[i] * A[i] + B[i] * B[i]);
        double temp2 = temp1 - C[i];
        double temp3 = temp2 + D[i];
        double temp4 = temp3 + A[i];
        double temp5 = temp4 + B[i];
        double temp6 = temp5 + A[i];
        double result = temp6;
        out[i] = result;
        i++;
    }
}