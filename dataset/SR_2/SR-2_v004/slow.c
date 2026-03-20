double slow_sr2_v004(double *X, double *Y, double *Z, int n, double alpha, double beta, double gamma) {
    double result = 0.0;
    int i = 0;
    while (i < n) {
        result += alpha * X[i] * X[i] * X[i] + gamma * X[i] * X[i] * X[i] + beta * Z[i] * Z[i] * Z[i] + beta * Z[i];
        i++;
    }
    return result;
}