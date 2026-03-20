void slow_sr3_v001(float *data, float *result, int n) {
    for (int i = 0; i < n; i++) {
        float ema = data[0];
        for (int j = 1; j <= i; j++)
            ema = 0.5f * data[j] + (1.0f - 0.5f) * ema;
        result[i] = ema;
    }
}