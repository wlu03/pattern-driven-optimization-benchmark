static double expensive_fn_v003(int key) {
    double r = 1.0;
    for (int i = 0; i < 200; i++) {
        r = exp(-fabs(r * 0.01)) + (double)(key % (i+1));
    }
    return r;
}

void fast_sr4_v003(double *arr, int n, int key) {
    double f0 = expensive_fn_v003(key);
    for (int i = 0; i < n; i++) {
        arr[i] *= f0;
    }
}