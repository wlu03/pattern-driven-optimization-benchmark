void fast_sr4_v009(float *arr, int n, int key) {
    float f0 = expensive_fn_v009(key);
    int i = 0;
    while (i < n) {
        arr[i] *= f0;
        i++;
    }
}