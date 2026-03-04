float expensive_fn_v048(int key) {
    float r = 0.0f;
    for (int i = 1; i <= 200; i++)
        r += log((float)(key + i));
    return r;
}

void slow_sr4_v048(float *arr, int n, int key) {
    int i = 0;
    while (i < n) {
        float f0 = expensive_fn_v048(key);
        arr[i] += f0;
        i++;
    }
}