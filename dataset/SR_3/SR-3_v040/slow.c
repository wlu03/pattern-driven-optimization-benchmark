void slow_sr3_v040(float *data, float *result, int n) {
    for (int i = 0; i < n; i++) {
        float ema = data[0];
        for (int j = 1; j <= i; j++)
            ema = 0.3f * data[j] + (1.0f - 0.3f) * ema;
        result[i] = ema;
    }
}