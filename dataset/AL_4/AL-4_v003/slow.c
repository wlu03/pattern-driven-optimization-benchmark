#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
long long slow_al4_v003(int r, int c) {
    if (r == 0 || c == 0) return 1;
    return slow_al4_v003(r-1, c) + slow_al4_v003(r, c-1);
}