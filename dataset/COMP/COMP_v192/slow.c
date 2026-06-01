static __attribute__((noinline)) long dp_rec_v192(int i, int j){
    if (i == 0 || j == 0) return 1;
    return dp_rec_v192(i-1, j) + dp_rec_v192(i, j-1);
}
long slow_comp_v192(int rows, int cols, int n_runs) {
    long acc = 0;
    for (int r = 0; r < n_runs; r++) {
        for (int j = 0; j < cols; j++) {
            for (int i = 0; i < rows; i++) {
                acc += dp_rec_v192(i, j);
            }
        }
    }
    return acc;
}