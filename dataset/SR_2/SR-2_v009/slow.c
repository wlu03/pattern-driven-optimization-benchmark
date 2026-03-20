double penalty_sr2_v009(double a, double b);

double slow_sr2_v009(double *X, double *Y, int n, double alpha, double beta) {
    double result = 0.0;
    int i = 0;
    while (i < n) {
        result += alpha * X[i] + alpha * Y[i] + penalty_sr2_v009(alpha, beta);
        i++;
    }
    return result;
}