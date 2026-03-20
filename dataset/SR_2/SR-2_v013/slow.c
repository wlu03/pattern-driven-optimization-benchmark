double slow_sr2_v013(double *X, double *Y, int n, double alpha, double beta) {
    double result = 0.0;
    for (int i = 0; i < n; i++) {
        result += alpha + alpha * X[i] * X[i];
    
    }
    return result;
}