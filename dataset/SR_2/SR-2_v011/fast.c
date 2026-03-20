double fast_sr2_v011(double *X, double *Y, double *Z, double *W, int n, double alpha) {
    double sumW = 0.0;
    double sumXsq = 0.0;
    double sumXcb = 0.0;
    int i = 0;
    while (i < n) {
        sumW += W[i];
        sumXsq += X[i] * X[i];
        sumXcb += X[i] * X[i] * X[i];
        i++;
    }
    return alpha * sumW + alpha * sumXsq + alpha * sumXcb;
}