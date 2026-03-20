double fast_sr2_v012(double *X, double *Y, double *Z, double *W, int n, double alpha, double beta) {
    double sumX = 0.0;
    double sumZsq = 0.0;
    int i = 0;
    while (i < n) {
        sumX += X[i];
        sumZsq += Z[i] * Z[i];
        i++;
    }
    return beta * sumX + alpha * sumZsq + (double)n * alpha;
}