double slow_sr2_v000(double *X, double *Y, int n, double alpha) {
    double result = 0.0;
    int i = 0;
    while (i < n) {
        result += alpha * Y[i] + alpha;
        i++;
    }
    return result;
}