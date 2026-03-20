double penalty_sr2_v015(double a, double b);

double fast_sr2_v015(double *X, double *Y, double *Z, int n, double alpha, double beta) {
    double p = penalty_sr2_v015(alpha, beta);
    double result = 0.0;
    int i = 0;
    while (i < n) {
        result += alpha * X[i] + alpha * Y[i] + alpha * Z[i];
        i++;
    }
    return result + (double)n * p;
}