#include <math.h>
__attribute__((noinline))
void slow_hr1_v020(float *out, float *A, float *B, float *C, int n) {
    for (int i = 0; i < n; i++) {
        float temp1 = (float)sqrt(A[i] * A[i] + B[i] * B[i]);
        float temp2 = temp1 - C[i];
        float temp3 = temp2 + A[i];
        float temp4 = temp3 + B[i];
        float temp5 = temp4 + A[i];
        float result = temp5;
        out[i] = result;
    }
}