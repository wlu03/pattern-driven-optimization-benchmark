int fast_al1_v045(int *grid, int m, int n, int r_unused, int c_unused) {
    int *dp = calloc(m * n, sizeof(int));
    dp[0] = grid[0];
    for (int j = 1; j < n; j++) dp[j] = dp[j-1] + grid[j];
    for (int i = 1; i < m; i++) {
        dp[i*n] = dp[(i-1)*n] + grid[i*n];
        for (int j = 1; j < n; j++) {
            int up = dp[(i-1)*n + j], left = dp[i*n + j - 1];
            dp[i*n + j] = grid[i*n + j] + ((up < left) ? up : left);
        }
    }
    int res = dp[m*n - 1]; free(dp); return res;
}