double slow_comp_v015(double *A, double *B, int n, double k, int mode) {
    double total = 0.0;
    for (int i = 0; i < n; i++) {
        // Pattern CF-1: Branch on invariant `mode`
        double val;
        if (mode == 1) val = A[i] + B[i] * k;      // Pattern SR-1
        else if (mode == 2) val = A[i] - B[i] * k;  // Pattern SR-1
        else val = A[i] * B[i] * k;                  // Pattern SR-1
        total += val;
    }
    return total;
}