float expensive_sr1_v004(int key);

void fast_sr1_v004(float *arr, int n, int key0, int key1, int key2, int key3) {
    float f0 = expensive_sr1_v004(key0);
    float f1 = expensive_sr1_v004(key1);
    float f2 = expensive_sr1_v004(key2);
    float f3 = expensive_sr1_v004(key3);
    for (int i = 0; i < n; i++) {
        arr[i] += f0 * f1 * f2 * f3;
    }
}