#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
void ds1_build_v021(int *hk, int *hv, int *ho, int hs, int *keys, int *values, int n);

int fast_ds1_v021(int *hk, int *hv, int *ho, int hs, int target) {
    unsigned h = (unsigned)target & (unsigned)(hs - 1);
    while (ho[h]) {
        if (hk[h] == target) return hv[h];
        h = (h + 1) & (unsigned)(hs - 1);
    }
    return -1;
}
void ds1_build_v021(int *hk, int *hv, int *ho, int hs, int *keys, int *values, int n) {
    for (int i = 0; i < n; i++) {
        unsigned h = (unsigned)keys[i] & (unsigned)(hs - 1);
        while (ho[h]) h = (h + 1) & (unsigned)(hs - 1);
        hk[h] = keys[i]; hv[h] = values[i]; ho[h] = 1;
    }
}