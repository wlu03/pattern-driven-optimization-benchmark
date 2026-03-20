void fast_sr3_v002(float *data, float *result, int n) {
    result[0] = data[0];
    for (int i = 1; i < n; i++) {
        result[i] = 0.1f * data[i] + (1.0f - 0.1f) * result[i-1];
    }
}