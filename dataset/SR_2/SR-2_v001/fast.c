double fast_sr2_v001(double *X, double *Y, double *Z, int n, double alpha) {
    double sumYsq = 0.0;
    double sumX = 0.0;
    for (int i = 0; i < n; i++) {
        sumYsq += Y[i] * Y[i];
        sumX += X[i];
    }
    return alpha * sumYsq + alpha * sumX;
}