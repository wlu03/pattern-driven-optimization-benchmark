#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
long long slow_al1_v025(int n) {
    if (n <= 0) return (n == 0) ? 1 : 0;
    return slow_al1_v025(n-1) + slow_al1_v025(n-2) + slow_al1_v025(n-3) + slow_al1_v025(n-4) + slow_al1_v025(n-5);
}