void fast_sr3_v011(float *data, float *result, int n) {
    float sum = 0.0f;
    int i = 0;
    while (i < n) {
        sum += data[i];
        if (i >= 64) sum -= data[i - 64];
        result[i] = sum;
        i++;
    }
}