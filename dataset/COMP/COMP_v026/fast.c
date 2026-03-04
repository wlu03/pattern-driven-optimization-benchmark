double fast_comp_v026(double *arr, int n, int key) {
    if (arr == NULL || n <= 0) return 0.0;
    // Fix SR-4: Hoist invariant call
    double factor = config_val_v026(key);
    // Fix HR-4: Remove redundant checks
    double sum = 0.0;
    for (int i = 0; i < n; i++) sum += arr[i] * factor;
    return sum;
}