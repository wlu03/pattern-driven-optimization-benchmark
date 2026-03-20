float expensive_sr1_v000(int key);

void fast_sr1_v000(float *arr, int n, int key0, int key1, int key2) {
    float f0 = expensive_sr1_v000(key0);
    float f1 = expensive_sr1_v000(key1);
    float f2 = expensive_sr1_v000(key2);
    for (int i = 0; i < n; i++) {
        arr[i] *= f0 * f1 * f2;
    }
}