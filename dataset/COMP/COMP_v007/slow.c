static __attribute__((noinline)) double penalty_v007(double a, double b){
    volatile double _a=a,_b=b; /* block pure/const inference */
    double r = 0.0;
    for(int k=1;k<=20;k++) r+=sin(_a*k)*exp(-_b*k*0.05);
    return r;
}
double slow_comp_v007(double *X, double *Y, int n, double alpha, double beta) {
    double result = 0;
    for (int i = 0; i < n; i++) {
        double t1 = X[i] * X[i];
        double t2 = alpha * t1;
        double t3 = beta * Y[i];
        double t4 = t2 + t3;
        double pen = (double)penalty_v007((double)alpha, (double)beta);
        result += t4 + pen;
    }
    return result;
}