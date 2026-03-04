void fast_sr3_v024(float *data, float *result, int n) {
    float mx = data[0];
    result[0] = mx;
    for (int i = 1; i < n; i++) {
        if (data[i] > mx) mx = data[i];
        result[i] = mx;
    }
}