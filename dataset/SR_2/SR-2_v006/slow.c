double slow_sr2_v006(double *X, double *Y, double *Z, int n, double alpha) {
    double result = 0.0;
    int i = 0;
    while (i < n) {
        result += alpha * X[i] * X[i] * X[i] + alpha * Z[i] * Z[i] * Z[i];
        i++;
    }
    return result;
}