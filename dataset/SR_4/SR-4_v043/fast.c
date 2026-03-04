void fast_sr4_v043(double *arr, int n, int key0, int key1) {
    double f0 = expensive_fn_v043(key0);
    double f1 = expensive_fn_v043(key1);
    int i = 0;
    while (i < n) {
        arr[i] *= f0 * f1;
        i++;
    }
}