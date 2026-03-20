void fast_sr3_v001(float *data, float *result, int n) {
    result[0] = data[0];
    for (int i = 1; i < n; i++) {
        result[i] = 0.5f * data[i] + (1.0f - 0.5f) * result[i-1];
    }
}