double expensive_sr1_v002(int key);

void slow_sr1_v002(double *arr, int n, int key) {
    for (int i = 0; i < n; i++) {
        double f0 = expensive_sr1_v002(key);
        arr[i] *= f0;
    }
}