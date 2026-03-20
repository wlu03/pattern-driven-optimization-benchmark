static double expensive_fn_v003(int key) {
    double r = 1.0;
    for (int i = 0; i < 200; i++) {
        r = exp(-fabs(r * 0.01)) + (double)(key % (i+1));
    }
    return r;
}

void slow_sr4_v003(double *arr, int n, int key) {
    for (int i = 0; i < n; i++) {
        double f0 = expensive_fn_v003(key);
        arr[i] *= f0;
    }
}