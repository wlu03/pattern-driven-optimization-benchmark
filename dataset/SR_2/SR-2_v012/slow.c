double slow_sr2_v012(double *X, double *Y, double *Z, double *W, int n, double alpha, double beta) {
    double result = 0.0;
    int i = 0;
    while (i < n) {
        result += beta * X[i] + alpha * Z[i] * Z[i] + alpha;
        i++;
    }
    return result;
}