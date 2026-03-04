void fast_sr3_v042(int *data, int *result, int n) {
    int mx = data[0];
    result[0] = mx;
    for (int i = 1; i < n; i++) {
        if (data[i] > mx) mx = data[i];
        result[i] = mx;
    }
}