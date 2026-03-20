#include <stdio.h>
#include <stdlib.h>
#include <math.h>
float slow_sr2_v006(float *X, float *Y, float *Z, float *W, int n, float alpha, float beta);
float fast_sr2_v006(float *X, float *Y, float *Z, float *W, int n, float alpha, float beta);
int main() {
    int n = 5000000;
    float *X = malloc(5000000 * sizeof(float)); for (int k = 0; k < 5000000; k++) X[k] = (float)(k % 100) * 0.01f;
    float *Y = malloc(5000000 * sizeof(float)); for (int k = 0; k < 5000000; k++) Y[k] = (float)(k % 100) * 0.01f;
    float *Z = malloc(5000000 * sizeof(float)); for (int k = 0; k < 5000000; k++) Z[k] = (float)(k % 100) * 0.01f;
    float *W = malloc(5000000 * sizeof(float)); for (int k = 0; k < 5000000; k++) W[k] = (float)(k % 100) * 0.01f;
    float r_slow = slow_sr2_v006(X, Y, Z, W, n, 2.5, 1.7);
    float r_fast = fast_sr2_v006(X, Y, Z, W, n, 2.5, 1.7);
    double diff = fabs((double)(r_slow - r_fast));
    double rel = (fabs((double)r_slow) > 1e-15) ? diff / fabs((double)r_slow) : diff;
    printf("slow=%g fast=%g rel_err=%g %s\n", (double)r_slow, (double)r_fast, rel, rel < 1e-4 ? "PASS" : "FAIL");
    free(X);
    free(Y);
    free(Z);
    free(W);
    return rel < 1e-4 ? 0 : 1;
}
