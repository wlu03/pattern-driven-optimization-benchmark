double penalty_sr2_v002(double a, double b);

double fast_sr2_v002(double *X, double *Y, int n, double alpha, double beta) {
    double p = penalty_sr2_v002(alpha, beta);
    double result = 0.0;
    int i = 0;
    while (i < n) {
        result += alpha * X[i] + alpha * Y[i];
        i++;
    }
    return result + (double)n * p;
}