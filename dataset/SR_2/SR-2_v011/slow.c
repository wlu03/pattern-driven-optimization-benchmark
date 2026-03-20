double slow_sr2_v011(double *X, double *Y, double *Z, double *W, int n, double alpha) {
    double result = 0.0;
    int i = 0;
    while (i < n) {
        result += alpha * W[i] + alpha * X[i] * X[i] + alpha * X[i] * X[i] * X[i];
        i++;
    }
    return result;
}