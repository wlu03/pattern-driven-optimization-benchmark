#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
int fast_al1_v007(int coins[], int nc, int amount) {
    int *dp = calloc(amount+1, sizeof(int));
    dp[0] = 1;
    for (int a = 1; a <= amount; a++)
        for (int i = 0; i < nc; i++)
            if (coins[i] <= a) dp[a] += dp[a - coins[i]];
    int res = dp[amount]; free(dp); return res;
}