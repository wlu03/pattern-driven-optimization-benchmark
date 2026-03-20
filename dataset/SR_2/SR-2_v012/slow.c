double slow_sr2_v012(double *X, double *Y, int n, double alpha, double beta, double gamma) {
    double result = 0.0;
    int i = 0;
    while (i < n) {
        result += gamma * Y[i] + beta * X[i] + beta + alpha * X[i] * X[i] * X[i] + alpha;
        i++;
    }
    return result;
}