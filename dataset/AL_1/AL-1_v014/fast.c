long long fast_al1_v014(int r, int c) {
    long long *dp = calloc(c+1, sizeof(long long));
    for (int j = 0; j <= c; j++) dp[j] = 1;
    for (int i = 1; i <= r; i++)
        for (int j = 1; j <= c; j++)
            dp[j] += dp[j-1];
    long long res = dp[c]; free(dp); return res;
}