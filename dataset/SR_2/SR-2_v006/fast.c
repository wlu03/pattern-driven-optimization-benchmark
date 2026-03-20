double fast_sr2_v006(double *X, double *Y, double *Z, int n, double alpha) {
    double sumXcb = 0.0;
    double sumZcb = 0.0;
    int i = 0;
    while (i < n) {
        sumXcb += X[i] * X[i] * X[i];
        sumZcb += Z[i] * Z[i] * Z[i];
        i++;
    }
    return alpha * sumXcb + alpha * sumZcb;
}