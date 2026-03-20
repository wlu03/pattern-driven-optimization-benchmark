double fast_sr2_v002(double *X, double *Y, double *Z, int n, double alpha, double beta) {
    double sumYcb = 0.0;
    for (int i = 0; i < n; i++) {
        sumYcb += Y[i] * Y[i] * Y[i];
    }
    return (double)n * alpha + beta * sumYcb + (double)n * alpha;
}