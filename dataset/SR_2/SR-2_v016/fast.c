double penalty_sr2_v016(double a, double b);

double fast_sr2_v016(double *X, double *Y, double *Z, int n, double alpha, double beta) {
    double p = penalty_sr2_v016(alpha, beta);
    double result = 0.0;
    for (int i = 0; i < n; i++) {
        result += alpha * X[i] + alpha * Y[i] + alpha * Z[i];
    }
    return result + (double)n * p;
}