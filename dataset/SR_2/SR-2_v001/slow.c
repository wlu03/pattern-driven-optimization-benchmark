double slow_sr2_v001(double *X, double *Y, double *Z, int n, double alpha) {
    double result = 0.0;
    for (int i = 0; i < n; i++) {
        result += alpha * Y[i] * Y[i] + alpha * X[i];
    
    }
    return result;
}