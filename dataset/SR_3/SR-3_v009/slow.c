void slow_sr3_v009(float *data, float *result, int n) {
    for (int i = 0; i < n; i++) {
        float sum = 0.0f;
        int start = (i >= 4) ? i - 4 + 1 : 0;
        int count = i - start + 1;
        for (int j = start; j <= i; j++) sum += data[j];
        result[i] = sum / count;
    }
}