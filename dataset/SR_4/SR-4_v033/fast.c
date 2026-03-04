void fast_sr4_v033(float *arr, int n, int key) {
    float f0 = expensive_fn_v033(key);
    for (int i = 0; i < n; i++) {
        arr[i] *= f0;
    }
}