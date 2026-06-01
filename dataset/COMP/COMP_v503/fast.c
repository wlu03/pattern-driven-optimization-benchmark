long fast_comp_v503(int rows, int cols) {
    long *dp = (long*)malloc((size_t)rows * cols * sizeof(long));
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            if (i == 0 || j == 0) dp[i*cols+j] = 1;
            else dp[i*cols+j] = dp[(i-1)*cols+j] + dp[i*cols+(j-1)];
        }
    }
    long acc = 0;
    for (int i = 0; i < rows; i++)
        for (int j = 0; j < cols; j++) acc += dp[i*cols+j];
    free(dp);
    return acc;
}