void fast_sr3_v045(float *data, float *result, int n) {
    float sum = 0.0f;
    for (int i = 0; i < n; i++) {
        sum += data[i];
        result[i] = sum / (i + 1);
    }
}