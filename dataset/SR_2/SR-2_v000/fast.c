double fast_sr2_v000(double *X, double *Y, int n, double alpha) {
    double sumY = 0.0;
    int i = 0;
    while (i < n) {
        sumY += Y[i];
        i++;
    }
    return alpha * sumY + (double)n * alpha;
}