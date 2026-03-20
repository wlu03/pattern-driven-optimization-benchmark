double penalty_sr2_v011(double a, double b);

double fast_sr2_v011(double *X, double *Y, int n, double alpha, double beta) {
    double p = penalty_sr2_v011(alpha, beta);
    double result = 0.0;
    for (int i = 0; i < n; i++) {
        result += alpha * X[i] + alpha * Y[i];
    }
    return result + (double)n * p;
}