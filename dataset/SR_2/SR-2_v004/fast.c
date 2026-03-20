double fast_sr2_v004(double *X, double *Y, int n, double alpha, double beta) {
    double sumXcb = 0.0;
    double sumYcb = 0.0;
    double sumY = 0.0;
    int i = 0;
    while (i < n) {
        sumXcb += X[i] * X[i] * X[i];
        sumYcb += Y[i] * Y[i] * Y[i];
        sumY += Y[i];
        i++;
    }
    return beta * sumXcb + (double)n * alpha + alpha * sumYcb + alpha * sumY;
}