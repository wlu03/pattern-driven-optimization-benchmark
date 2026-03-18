#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
long long slow_al1_v014(int n) {
    if (n == 0) return 0;
    if (n <= 2) return 1;
    return slow_al1_v014(n-1) + slow_al1_v014(n-2) + slow_al1_v014(n-3);
}