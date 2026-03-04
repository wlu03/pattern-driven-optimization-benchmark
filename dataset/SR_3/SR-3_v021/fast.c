void fast_sr3_v021(float *data, float *result, int n) {
    float sum = 0.0f;
    for (int i = 0; i < n; i++) {
        sum += data[i];
        if (i >= 8) sum -= data[i - 8];
        result[i] = sum;
    }
}