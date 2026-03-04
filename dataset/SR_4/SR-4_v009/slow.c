float expensive_fn_v009(int key) {
    float r = 0.0f;
    for (int i = 1; i <= 100; i++)
        r += log((float)(key + i));
    return r;
}

void slow_sr4_v009(float *arr, int n, int key) {
    int i = 0;
    while (i < n) {
        float f0 = expensive_fn_v009(key);
        arr[i] *= f0;
        i++;
    }
}