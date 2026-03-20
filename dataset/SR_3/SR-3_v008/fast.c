void fast_sr3_v008(float *data, float *result, int n) {
    result[0] = data[0];
    int i = 1;
    while (i < n) {
        result[i] = 0.3f * data[i] + (1.0f - 0.3f) * result[i-1];
        i++;
    }
}