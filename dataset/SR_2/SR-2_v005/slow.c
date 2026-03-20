double slow_sr2_v005(double *X, double *Y, int n, double alpha) {
    double result = 0.0;
    for (int i = 0; i < n; i++) {
        result += alpha * X[i] * X[i] * X[i] + alpha * X[i] * X[i] * X[i] + alpha * Y[i] * Y[i];
    
    }
    return result;
}