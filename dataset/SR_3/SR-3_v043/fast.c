void fast_sr3_v043(float *data, float *result, int n) {
    float sum_sq = 0.0f;
    for (int i = 0; i < n; i++) {
        sum_sq += data[i] * data[i];
        result[i] = sqrt(sum_sq / (i + 1));
    }
}