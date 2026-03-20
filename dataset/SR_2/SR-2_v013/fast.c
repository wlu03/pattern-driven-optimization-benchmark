double fast_sr2_v013(double *X, double *Y, int n, double alpha, double beta) {
    double sumXsq = 0.0;
    for (int i = 0; i < n; i++) {
        sumXsq += X[i] * X[i];
    }
    return (double)n * alpha + alpha * sumXsq;
}