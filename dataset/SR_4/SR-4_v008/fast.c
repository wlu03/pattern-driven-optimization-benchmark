static float expensive_fn_v008(int key) {
    float r = 0.0f;
    for (int i = 1; i <= 500; i++)
        r += log((float)(key + i));
    return r;
}

void fast_sr4_v008(float *arr, int n, int key0, int key1) {
    float f0 = expensive_fn_v008(key0);
    float f1 = expensive_fn_v008(key1);
    for (int i = 0; i < n; i++) {
        arr[i] += f0 * f1;
    }
}