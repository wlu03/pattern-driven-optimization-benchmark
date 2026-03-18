#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
long long fast_al1_v006(int n) {
    long long *dp = calloc(n+1, sizeof(long long));
    dp[0] = dp[1] = 1;
    for (int i = 2; i <= n; i++)
        for (int j = 0; j < i; j++)
            dp[i] += dp[j] * dp[i - 1 - j];
    long long res = dp[n]; free(dp); return res;
}