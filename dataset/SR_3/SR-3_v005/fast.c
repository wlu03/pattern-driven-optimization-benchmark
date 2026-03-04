void fast_sr3_v005(float *data, float *result, int n) {
    float sum = 0.0f;
    for (int i = 0; i < n; i++) {
        sum += data[i];
        if (i >= 32) sum -= data[i - 32];
        result[i] = sum;
    }
}