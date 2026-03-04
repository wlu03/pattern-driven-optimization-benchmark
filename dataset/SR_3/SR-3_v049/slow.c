void slow_sr3_v049(float *data, float *result, int n) {
    for (int i = 0; i < n; i++) {
        float mx = data[0];
        for (int j = 1; j <= i; j++) if (data[j] > mx) mx = data[j];
        result[i] = mx;
    }
}