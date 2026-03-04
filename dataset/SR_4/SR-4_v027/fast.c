void fast_sr4_v027(float *arr, int n, int key) {
    float f0 = expensive_fn_v027(key);
    for (int i = 0; i < n; i++) {
        arr[i] += f0;
    }
}