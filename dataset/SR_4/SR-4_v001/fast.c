void fast_sr4_v001(float *arr, int n, int key0, int key1) {
    float f0 = expensive_fn_v001(key0);
    float f1 = expensive_fn_v001(key1);
    for (int i = 0; i < n; i++) {
        arr[i] *= f0 * f1;
    }
}