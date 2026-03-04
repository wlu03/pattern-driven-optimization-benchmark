float expensive_fn_v023(int key) {
    float r = 0.0f;
    for (int i = 0; i < 30; i++)
        r += sin((float)(key + i)) * cos((float)(key - i));
    return r;
}

void slow_sr4_v023(float *arr, int n, int key0, int key1, int key2) {
    int i = 0;
    while (i < n) {
        float f0 = expensive_fn_v023(key0);
        float f1 = expensive_fn_v023(key1);
        float f2 = expensive_fn_v023(key2);
        arr[i] *= f0 * f1 * f2;
        i++;
    }
}