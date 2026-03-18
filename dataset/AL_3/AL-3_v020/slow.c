#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
int slow_al3_v020(unsigned char *text, int tn,
                                unsigned char *pattern, int pn) {
    int count = 0;
    for (int i = 0; i <= tn - pn; i++) {
        int j;
        for (j = 0; j < pn; j++) {
            if (text[i + j] != pattern[j]) break;
        }
        if (j == pn) count++;
    }
    return count;
}