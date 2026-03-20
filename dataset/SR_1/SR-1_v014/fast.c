double expensive_sr1_v014(int key);

void fast_sr1_v014(double *arr, int n, int key0, int key1, int key2, int key3) {
    double f0 = expensive_sr1_v014(key0);
    double f1 = expensive_sr1_v014(key1);
    double f2 = expensive_sr1_v014(key2);
    double f3 = expensive_sr1_v014(key3);
    int i = 0;
    while (i < n) {
        arr[i] += f0 * f1 * f2 * f3;
        i++;
    }
}