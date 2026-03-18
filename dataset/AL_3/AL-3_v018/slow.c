#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
int slow_al3_v018(int *text, int tn, int *pattern, int pn) {
    int count = 0;
    for (int i = 0; i <= tn - pn; i++) {
        int match = 1;
        for (int j = 0; j < pn; j++) {
            if (text[i + j] != pattern[j]) { match = 0; break; }
        }
        if (match) count++;
    }
    return count;
}