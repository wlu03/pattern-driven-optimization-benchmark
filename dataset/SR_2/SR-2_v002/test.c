#include <stdio.h>
#include <stdlib.h>
#include <math.h>
float slow_sr2_v002(float *X, float *Y, int n, float alpha, float beta, float gamma);
float fast_sr2_v002(float *X, float *Y, int n, float alpha, float beta, float gamma);
int main() {
    int n = 20000000;
    float *X = malloc(20000000 * sizeof(float)); for (int k = 0; k < 20000000; k++) X[k] = (float)(k % 100) * 0.01f;
    float *Y = malloc(20000000 * sizeof(float)); for (int k = 0; k < 20000000; k++) Y[k] = (float)(k % 100) * 0.01f;
    float r_slow = slow_sr2_v002(X, Y, n, 2.5, 1.7, 0.3);
    float r_fast = fast_sr2_v002(X, Y, n, 2.5, 1.7, 0.3);
    double diff = fabs((double)(r_slow - r_fast));
    double rel = (fabs((double)r_slow) > 1e-15) ? diff / fabs((double)r_slow) : diff;
    printf("slow=%g fast=%g rel_err=%g %s\n", (double)r_slow, (double)r_fast, rel, rel < 1e-4 ? "PASS" : "FAIL");
    free(X);
    free(Y);
    return rel < 1e-4 ? 0 : 1;
}
