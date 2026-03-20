void slow_sr3_v009(float *data, float *result, int n) {
    for (int i = 0; i < n; i++) {
        float sum = 0.0f;
        for (int j = 0; j <= i; j++) sum += data[j];
        result[i] = sum;
    }
}