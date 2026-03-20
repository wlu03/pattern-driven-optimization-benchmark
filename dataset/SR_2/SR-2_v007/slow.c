double penalty_sr2_v007(double a, double b);

double slow_sr2_v007(double *X, double *Y, double *Z, int n, double alpha, double beta) {
    double result = 0.0;
    for (int i = 0; i < n; i++) {
        result += alpha * X[i] + alpha * Y[i] + alpha * Z[i] + penalty_sr2_v007(alpha, beta);
    }
    return result;
}