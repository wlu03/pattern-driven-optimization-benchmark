void fast_sr4_v012(double *arr, int n, int key) {
    double f0 = expensive_fn_v012(key);
    int i = 0;
    while (i < n) {
        arr[i] *= f0;
        i++;
    }
}