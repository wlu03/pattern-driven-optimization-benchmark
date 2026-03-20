double fast_sr2_v005(double *X, double *Y, int n, double alpha) {
    double sumXcb = 0.0;
    double sumYsq = 0.0;
    for (int i = 0; i < n; i++) {
        sumXcb += X[i] * X[i] * X[i];
        sumYsq += Y[i] * Y[i];
    }
    return alpha * sumXcb + alpha * sumXcb + alpha * sumYsq;
}