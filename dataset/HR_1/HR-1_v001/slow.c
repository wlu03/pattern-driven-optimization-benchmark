#include <math.h>
__attribute__((noinline))
void slow_hr1_v001(float *out, float *A, float *B, float *C, int n) {
    int i = 0;
    while (i < n) {
        float temp1 = (float)sqrt(A[i] * A[i] + B[i] * B[i]);
        float temp2 = temp1 * C[i];
        float temp3 = temp2 - A[i];
        float temp4 = temp3 - B[i];
        float temp5 = temp4 - C[i];
        float temp6 = temp5 - A[i];
        float result = temp6;
        out[i] = result;
        i++;
    }
}