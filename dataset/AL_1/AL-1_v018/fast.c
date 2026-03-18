#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
long long fast_al1_v018(int n) {
    if (n == 0) return 1;
    if (n == 1) return 0;
    long long a = 1, b = 0;
    for (int i = 2; i <= n; i++) {
        long long t = (i - 1) * (a + b);
        a = b; b = t;
    }
    return b;
}