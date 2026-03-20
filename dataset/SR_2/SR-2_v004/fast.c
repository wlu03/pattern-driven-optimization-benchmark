double fast_sr2_v004(double *X, double *Y, double *Z, int n, double alpha, double beta, double gamma) {
    double sumXcb = 0.0;
    double sumZcb = 0.0;
    double sumZ = 0.0;
    int i = 0;
    while (i < n) {
        sumXcb += X[i] * X[i] * X[i];
        sumZcb += Z[i] * Z[i] * Z[i];
        sumZ += Z[i];
        i++;
    }
    return alpha * sumXcb + gamma * sumXcb + beta * sumZcb + beta * sumZ;
}