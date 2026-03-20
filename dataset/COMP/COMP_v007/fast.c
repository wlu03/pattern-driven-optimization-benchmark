static __attribute__((noinline)) double penalty_v007(double a, double b){
    volatile double _a=a,_b=b; /* block pure/const inference */
    double r = 0.0;
    for(int k=1;k<=20;k++) r+=sin(_a*k)*exp(-_b*k*0.05);
    return r;
}
double fast_comp_v007(double *X, double *Y, int n, double alpha, double beta) {
    double pen = (double)penalty_v007((double)alpha, (double)beta);
    double sumXsq = 0, sumY = 0;
    for (int i = 0; i < n; i++) {
        sumXsq += X[i] * X[i];
        sumY += Y[i];
    }
    return alpha * sumXsq + beta * sumY + (double)n * pen;
}