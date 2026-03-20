#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define TN 10000000
#define PN 400

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    int *text=(int*)malloc(TN*sizeof(int));
    /* Adversarial text: all 1s with a 0 every (PN-1) positions.
       Pattern is all 1s ⇒ naive scans (PN-1) chars before each mismatch. */
    for(int i=0;i<TN;i++) text[i]=1;
    for(int i=PN-1;i<TN;i+=PN-1) text[i]=0;

    int *pat=(int*)malloc(PN*sizeof(int));
    for(int i=0;i<PN;i++) pat[i]=1;

    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    int cs=slow_al3_v005(text,TN,pat,PN);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;

    clock_gettime(CLOCK_MONOTONIC,&t0);
    int cf=fast_al3_v005(text,TN,pat,PN);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;

    int correct=(cs==cf);
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",
           ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(text);free(pat);return correct?0:1;
}