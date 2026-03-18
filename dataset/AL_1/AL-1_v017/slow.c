#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
long long slow_al1_v017(int n, int k) {
    if (k == 0 || k == n) return 1;
    return slow_al1_v017(n-1, k-1) + slow_al1_v017(n-1, k);
}