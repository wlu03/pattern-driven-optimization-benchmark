void fast_sr3_v016(float *data, float *result, int n) {
    float sum = 0.0f;
    float sum_sq = 0.0f;
    for (int i = 0; i < n; i++) {
        sum += data[i];
        sum_sq += data[i] * data[i];
        float mean = sum / (i + 1);
        result[i] = sum_sq / (i + 1) - mean * mean;
    }
}