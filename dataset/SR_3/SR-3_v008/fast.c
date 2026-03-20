void fast_sr3_v008(float *data, float *result, int n) {
    float sum = 0.0f;
    for (int i = 0; i < n; i++) {
        sum += data[i];
        if (i >= 128) sum -= data[i - 128];
        int count = (i < 128) ? i + 1 : 128;
        result[i] = sum / count;
    }
}