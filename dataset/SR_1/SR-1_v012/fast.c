float expensive_sr1_v012(int key);

void fast_sr1_v012(float *arr, int n, int key) {
    float f0 = expensive_sr1_v012(key);
    int i = 0;
    while (i < n) {
        arr[i] += f0;
        i++;
    }
}