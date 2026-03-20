double penalty_sr2_v011(double a, double b);

double slow_sr2_v011(double *X, double *Y, int n, double alpha, double beta) {
    double result = 0.0;
    for (int i = 0; i < n; i++) {
        result += alpha * X[i] + alpha * Y[i] + penalty_sr2_v011(alpha, beta);
    }
    return result;
}