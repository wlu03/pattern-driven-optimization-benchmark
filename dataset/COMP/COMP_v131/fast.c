static __attribute__((noinline)) double penalty_v131(double a, double b){
    volatile double _a=a,_b=b; /* block pure/const inference */
    double r = 0.0;
    for(int k=1;k<=20;k++) r+=sin(_a*k)*exp(-_b*k*0.05);
    return r;
}
int fast_comp_v131(int *X, int *Y, int n, int alpha, int beta) {
    int pen = (int)penalty_v131((double)alpha, (double)beta);
    int sumXsq = 0, sumY = 0;
    for (int i = 0; i < n; i++) {
        sumXsq += X[i] * X[i];
        sumY += Y[i];
    }
    return alpha * sumXsq + beta * sumY + (int)n * pen;
}