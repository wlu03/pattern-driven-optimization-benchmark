double slow_sr2_v004(double *X, double *Y, int n, double alpha, double beta) {
    double result = 0.0;
    int i = 0;
    while (i < n) {
        result += beta * X[i] * X[i] * X[i] + alpha + alpha * Y[i] * Y[i] * Y[i] + alpha * Y[i];
        i++;
    }
    return result;
}