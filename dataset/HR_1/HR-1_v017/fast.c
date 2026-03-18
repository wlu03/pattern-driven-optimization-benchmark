#include <math.h>
__attribute__((noinline))
void fast_hr1_v017(int *out, int *A, int *B, int *C, int n) {
    int i = 0;
    while (i < n) {
        out[i] = (((int)sqrt(A[i] * A[i] + B[i] * B[i])) - C[i]) - A[i];
        i++;
    }
}