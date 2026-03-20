double slow_sr2_v005(double *X, double *Y, int n, double alpha) {
    double result = 0.0;
    for (int i = 0; i < n; i++) {
        result += alpha * X[i] + alpha * Y[i] + alpha * Y[i] * Y[i] * Y[i] + alpha * Y[i] * Y[i];
    
    }
    return result;
}