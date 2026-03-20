float expensive_sr1_v007(int key);

void fast_sr1_v007(float *arr, int n, int key0, int key1, int key2) {
    float f0 = expensive_sr1_v007(key0);
    float f1 = expensive_sr1_v007(key1);
    float f2 = expensive_sr1_v007(key2);
    int i = 0;
    while (i < n) {
        arr[i] *= f0 * f1 * f2;
        i++;
    }
}