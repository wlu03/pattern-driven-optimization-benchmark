double penalty_sr2_v001(double a, double b);

double slow_sr2_v001(double *X, double *Y, double *Z, int n, double alpha, double beta) {
    double result = 0.0;
    int i = 0;
    while (i < n) {
        result += alpha * X[i] + alpha * Y[i] + alpha * Z[i] + penalty_sr2_v001(alpha, beta);
        i++;
    }
    return result;
}