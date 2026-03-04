void fast_sr4_v048(float *arr, int n, int key) {
    float f0 = expensive_fn_v048(key);
    int i = 0;
    while (i < n) {
        arr[i] += f0;
        i++;
    }
}