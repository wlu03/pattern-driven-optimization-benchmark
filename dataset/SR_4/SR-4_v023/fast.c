void fast_sr4_v023(float *arr, int n, int key0, int key1, int key2) {
    float f0 = expensive_fn_v023(key0);
    float f1 = expensive_fn_v023(key1);
    float f2 = expensive_fn_v023(key2);
    int i = 0;
    while (i < n) {
        arr[i] *= f0 * f1 * f2;
        i++;
    }
}