#include <math.h>
__attribute__((noinline))
void slow_hr1_v014(int *out, int *A, int *B, int *C, int n) {
    int i = 0;
    while (i < n) {
        int temp1 = (int)sqrt(A[i] * A[i] + B[i] * B[i]);
        int temp2 = temp1 + C[i];
        int temp3 = temp2 * A[i];
        int result = temp3;
        out[i] = result;
        i++;
    }
}