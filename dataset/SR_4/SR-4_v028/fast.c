void fast_sr4_v028(float *arr, int n, int key0, int key1, int key2, int key3) {
    float f0 = expensive_fn_v028(key0);
    float f1 = expensive_fn_v028(key1);
    float f2 = expensive_fn_v028(key2);
    float f3 = expensive_fn_v028(key3);
    int i = 0;
    while (i < n) {
        arr[i] *= f0 * f1 * f2 * f3;
        i++;
    }
}