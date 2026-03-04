void fast_sr4_v034(float *arr, int n, int key0, int key1, int key2) {
    float f0 = expensive_fn_v034(key0);
    float f1 = expensive_fn_v034(key1);
    float f2 = expensive_fn_v034(key2);
    for (int i = 0; i < n; i++) {
        arr[i] += f0 * f1 * f2;
    }
}