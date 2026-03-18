#include <math.h>
__attribute__((noinline))
void slow_hr1_v010(float *out, float *A, float *B, float *C, float *D, int n) {
    for (int i = 0; i < n; i++) {
        float temp1 = (float)sqrt(A[i] * A[i] + B[i] * B[i]);
        float temp2 = temp1 + A[i];
        float result = temp2;
        out[i] = result;
    }
}