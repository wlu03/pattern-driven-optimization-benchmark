void fast_sr3_v032(float *data, float *result, int n) {
    float sum = 0.0f;
    int i = 0;
    while (i < n) {
        sum += data[i];
        if (i >= 32) sum -= data[i - 32];
        result[i] = sum;
        i++;
    }
}