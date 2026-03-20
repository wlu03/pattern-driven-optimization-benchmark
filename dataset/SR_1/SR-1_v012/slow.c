float expensive_sr1_v012(int key);

void slow_sr1_v012(float *arr, int n, int key) {
    int i = 0;
    while (i < n) {
        float f0 = expensive_sr1_v012(key);
        arr[i] += f0;
        i++;
    }
}