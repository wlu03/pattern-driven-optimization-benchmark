long fast_comp_v352(int rows, int cols, int n_runs) {
    long *dp = (long*)malloc(rows * cols * sizeof(long));
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            if (i == 0 || j == 0) dp[i*cols+j] = 1;
            else dp[i*cols+j] = dp[(i-1)*cols+j] + dp[i*cols+(j-1)];
        }
    }
    long total = 0;
    for (int i = 0; i < rows; i++)
        for (int j = 0; j < cols; j++) total += dp[i*cols+j];
    free(dp);
    return total * (long)n_runs;
}