#include <math.h>
__attribute__((noinline))
void slow_hr1_v021(float *out, float *A, float *B, float *C, float *D, int n) {
    int i = 0;
    while (i < n) {
        float temp1 = (float)sqrt(A[i] * A[i] + B[i] * B[i]);
        float temp2 = temp1 + A[i];
        float result = temp2;
        out[i] = result;
        i++;
    }
}