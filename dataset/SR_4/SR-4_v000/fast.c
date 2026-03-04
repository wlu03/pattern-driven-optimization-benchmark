void fast_sr4_v000(float *arr, int n, int key0, int key1) {
    float f0 = expensive_fn_v000(key0);
    float f1 = expensive_fn_v000(key1);
    int i = 0;
    while (i < n) {
        arr[i] *= f0 * f1;
        i++;
    }
}