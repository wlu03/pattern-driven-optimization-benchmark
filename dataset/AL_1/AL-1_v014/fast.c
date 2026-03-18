#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
long long fast_al1_v014(int n) {
    if (n == 0) return 0;
    if (n <= 2) return 1;
    long long a=0, b=1, c=1;
    for (int i=3; i<=n; i++) { long long t=a+b+c; a=b; b=c; c=t; }
    return c;
}