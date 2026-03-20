static __attribute__((noinline)) double penalty_v016(double a, double b){
    volatile double _a=a,_b=b; /* block pure/const inference */
    double r = 0.0;
    for(int k=1;k<=20;k++) r+=sin(_a*k)*exp(-_b*k*0.05);
    return r;
}
float slow_comp_v016(float *X, float *Y, int n, float alpha, float beta) {
    float result = 0;
    for (int i = 0; i < n; i++) {
        float t1 = X[i] * X[i];
        float t2 = alpha * t1;
        float t3 = beta * Y[i];
        float t4 = t2 + t3;
        float pen = (float)penalty_v016((double)alpha, (double)beta);
        result += t4 + pen;
    }
    return result;
}