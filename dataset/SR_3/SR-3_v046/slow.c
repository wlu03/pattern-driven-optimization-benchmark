void slow_sr3_v046(int *data, int *result, int n) {
    for (int i = 0; i < n; i++) {
        int mn = data[0];
        for (int j = 1; j <= i; j++) if (data[j] < mn) mn = data[j];
        result[i] = mn;
    }
}