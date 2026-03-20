#include <stdio.h>
#include <stdlib.h>
#include <math.h>
double slow_sr2_v004(double *X, double *Y, double *Z, int n, double alpha, double beta, double gamma);
double fast_sr2_v004(double *X, double *Y, double *Z, int n, double alpha, double beta, double gamma);
int main() {
    int n = 20000000;
    double *X = malloc(20000000 * sizeof(double)); for (int k = 0; k < 20000000; k++) X[k] = (double)(k % 100) * 0.01f;
    double *Y = malloc(20000000 * sizeof(double)); for (int k = 0; k < 20000000; k++) Y[k] = (double)(k % 100) * 0.01f;
    double *Z = malloc(20000000 * sizeof(double)); for (int k = 0; k < 20000000; k++) Z[k] = (double)(k % 100) * 0.01f;
    double r_slow = slow_sr2_v004(X, Y, Z, n, 2.5, 1.7, 0.3);
    double r_fast = fast_sr2_v004(X, Y, Z, n, 2.5, 1.7, 0.3);
    double diff = fabs((double)(r_slow - r_fast));
    double rel = (fabs((double)r_slow) > 1e-15) ? diff / fabs((double)r_slow) : diff;
    printf("slow=%g fast=%g rel_err=%g %s\n", (double)r_slow, (double)r_fast, rel, rel < 1e-4 ? "PASS" : "FAIL");
    free(X);
    free(Y);
    free(Z);
    return rel < 1e-4 ? 0 : 1;
}
