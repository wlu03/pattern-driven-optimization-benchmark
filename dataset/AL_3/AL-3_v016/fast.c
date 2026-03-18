#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
static void build_fail_v016(int *pat, int pn, int *fail);

int fast_al3_v016(int *text, int tn, int *pattern, int pn) {
    int *fail = malloc(pn * sizeof(int));
    build_fail_v016(pattern, pn, fail);
    int count = 0, k = 0;
    for (int i = 0; i < tn; i++) {
        while (k > 0 && pattern[k] != text[i]) k = fail[k-1];
        if (pattern[k] == text[i]) k++;
        if (k == pn) { count++; k = fail[k-1]; }
    }
    free(fail);
    return count;
}
static void build_fail_v016(int *pat, int pn, int *fail) {
    fail[0] = 0;
    int k = 0;
    for (int i = 1; i < pn; i++) {
        while (k > 0 && pat[k] != pat[i]) k = fail[k-1];
        if (pat[k] == pat[i]) k++;
        fail[i] = k;
    }
}