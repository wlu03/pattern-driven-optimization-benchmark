#include <math.h>
__attribute__((noinline))
void slow_hr1_v028(double *out, double *A, double *B, double *C, int n) {
    int i = 0;
    while (i < n) {
        double temp1 = (double)sqrt(A[i] * A[i] + B[i] * B[i]);
        double temp2 = temp1 + C[i];
        double temp3 = temp2 * A[i];
        double temp4 = temp3 - B[i];
        double temp5 = temp4 - A[i];
        double result = temp5;
        out[i] = result;
        i++;
    }
}