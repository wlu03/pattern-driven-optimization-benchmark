void fast_sr4_v038(float *arr, int n, int key0, int key1) {
    float f0 = expensive_fn_v038(key0);
    float f1 = expensive_fn_v038(key1);
    for (int i = 0; i < n; i++) {
        arr[i] += f0 * f1;
    }
}