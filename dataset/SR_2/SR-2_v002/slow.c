double slow_sr2_v002(double *X, double *Y, double *Z, int n, double alpha, double beta) {
    double result = 0.0;
    for (int i = 0; i < n; i++) {
        result += alpha + beta * Y[i] * Y[i] * Y[i] + alpha;
    
    }
    return result;
}