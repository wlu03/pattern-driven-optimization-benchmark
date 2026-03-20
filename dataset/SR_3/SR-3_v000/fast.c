void fast_sr3_v000(float *data, float *result, int n) {
    float sum = 0.0f;
    float sum_sq = 0.0f;
    int i = 0;
    while (i < n) {
        sum += data[i];
        sum_sq += data[i] * data[i];
        float mean = sum / (i + 1);
        result[i] = sum_sq / (i + 1) - mean * mean;
        i++;
    }
}