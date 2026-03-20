static float expensive_fn_v000(int key) {
    unsigned int h = (unsigned int)key;
    float r = 0.0f;
    for (int i = 0; i < 50; i++) {
        h = h * 2654435761u;
        r += (float)(h & 0xFFFF) / 65536.0f;
    }
    return r / 50;
}

void slow_sr4_v000(float *arr, int n, int key) {
    for (int i = 0; i < n; i++) {
        float f0 = expensive_fn_v000(key);
        arr[i] *= f0;
    }
}