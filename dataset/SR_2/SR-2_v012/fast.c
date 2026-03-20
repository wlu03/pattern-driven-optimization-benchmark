double fast_sr2_v012(double *X, double *Y, int n, double alpha, double beta, double gamma) {
    double sumY = 0.0;
    double sumX = 0.0;
    double sumXcb = 0.0;
    int i = 0;
    while (i < n) {
        sumY += Y[i];
        sumX += X[i];
        sumXcb += X[i] * X[i] * X[i];
        i++;
    }
    return gamma * sumY + beta * sumX + (double)n * beta + alpha * sumXcb + (double)n * alpha;
}