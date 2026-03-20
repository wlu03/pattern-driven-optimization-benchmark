double expensive_sr1_v009(int key);

void slow_sr1_v009(double *arr, int n, int key0, int key1, int key2) {
    for (int i = 0; i < n; i++) {
        double f0 = expensive_sr1_v009(key0);
        double f1 = expensive_sr1_v009(key1);
        double f2 = expensive_sr1_v009(key2);
        arr[i] += f0 * f1 * f2;
    }
}