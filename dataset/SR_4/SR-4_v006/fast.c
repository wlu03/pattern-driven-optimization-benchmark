void fast_sr4_v006(float *arr, int n, int key0, int key1, int key2, int key3) {
    float f0 = expensive_fn_v006(key0);
    float f1 = expensive_fn_v006(key1);
    float f2 = expensive_fn_v006(key2);
    float f3 = expensive_fn_v006(key3);
    for (int i = 0; i < n; i++) {
        arr[i] *= f0 * f1 * f2 * f3;
    }
}