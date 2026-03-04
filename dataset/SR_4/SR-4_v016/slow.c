float expensive_fn_v016(int key) {
    float r = 0.0f;
    for (int i = 0; i < 1000; i++)
        r += sin((float)(key + i)) * cos((float)(key - i));
    return r;
}

void slow_sr4_v016(float *arr, int n, int key0, int key1, int key2) {
    for (int i = 0; i < n; i++) {
        float f0 = expensive_fn_v016(key0);
        float f1 = expensive_fn_v016(key1);
        float f2 = expensive_fn_v016(key2);
        arr[i] += f0 * f1 * f2;
    }
}