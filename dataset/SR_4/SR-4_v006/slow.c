static double expensive_fn_v006(int key) {
    double r = 1.0;
    for (int i = 0; i < 50; i++) {
        r = exp(-fabs(r * 0.01)) + (double)(key % (i+1));
    }
    return r;
}

void slow_sr4_v006(double *arr, int n, int key0, int key1) {
    for (int i = 0; i < n; i++) {
        double f0 = expensive_fn_v006(key0);
        double f1 = expensive_fn_v006(key1);
        arr[i] *= f0 * f1;
    }
}