double fast_sr2_v005(double *X, double *Y, int n, double alpha) {
    double sumX = 0.0;
    double sumY = 0.0;
    double sumYcb = 0.0;
    double sumYsq = 0.0;
    for (int i = 0; i < n; i++) {
        sumX += X[i];
        sumY += Y[i];
        sumYcb += Y[i] * Y[i] * Y[i];
        sumYsq += Y[i] * Y[i];
    }
    return alpha * sumX + alpha * sumY + alpha * sumYcb + alpha * sumYsq;
}