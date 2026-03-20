#include <stdio.h>
#include <stdlib.h>
#include <math.h>
float slow_sr2_v009(float *X, float *Y, float *Z, int n, float alpha);
float fast_sr2_v009(float *X, float *Y, float *Z, int n, float alpha);
int main() {
    int n = 10000000;
    float *X = malloc(10000000 * sizeof(float)); for (int k = 0; k < 10000000; k++) X[k] = (float)(k % 100) * 0.01f;
    float *Y = malloc(10000000 * sizeof(float)); for (int k = 0; k < 10000000; k++) Y[k] = (float)(k % 100) * 0.01f;
    float *Z = malloc(10000000 * sizeof(float)); for (int k = 0; k < 10000000; k++) Z[k] = (float)(k % 100) * 0.01f;
    float r_slow = slow_sr2_v009(X, Y, Z, n, 2.5);
    float r_fast = fast_sr2_v009(X, Y, Z, n, 2.5);
    double diff = fabs((double)(r_slow - r_fast));
    double rel = (fabs((double)r_slow) > 1e-15) ? diff / fabs((double)r_slow) : diff;
    printf("slow=%g fast=%g rel_err=%g %s\n", (double)r_slow, (double)r_fast, rel, rel < 1e-4 ? "PASS" : "FAIL");
    free(X);
    free(Y);
    free(Z);
    return rel < 1e-4 ? 0 : 1;
}
