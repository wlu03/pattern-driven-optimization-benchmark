#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
long long slow_al4_v015(int n) {
    if (n <= 1) return n;
    return slow_al4_v015(n-1) + slow_al4_v015(n-2);
}