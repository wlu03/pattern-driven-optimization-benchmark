void fast_sr4_v020(float *arr, int n, int key) {
    float f0 = expensive_fn_v020(key);
    for (int i = 0; i < n; i++) {
        arr[i] *= f0;
    }
}