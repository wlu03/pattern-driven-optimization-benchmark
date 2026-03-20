static __attribute__((noinline)) double penalty_v131(double a, double b){
    volatile double _a=a,_b=b; /* block pure/const inference */
    double r = 0.0;
    for(int k=1;k<=20;k++) r+=sin(_a*k)*exp(-_b*k*0.05);
    return r;
}
int slow_comp_v131(int *X, int *Y, int n, int alpha, int beta) {
    int result = 0;
    for (int i = 0; i < n; i++) {
        int t1 = X[i] * X[i];
        int t2 = alpha * t1;
        int t3 = beta * Y[i];
        int t4 = t2 + t3;
        int pen = (int)penalty_v131((double)alpha, (double)beta);
        result += t4 + pen;
    }
    return result;
}