static __attribute__((noinline)) int expensive_check_v287(unsigned short qt){
    volatile unsigned short _q=qt; /* block ipa-pure-const */
    int r=0;
    for(int k=1;k<=200;k++) r += (int)((_q*k) & 0xFF);
    return r;
}
long slow_comp_v287(long *pointers, unsigned short *tags, int n, unsigned short *queries, int m) {
    long matches = 0;
    for (int q = 0; q < m; q++) {
        unsigned short qt = queries[q];
        for (int i = 0; i < n; i++) {
            unsigned short t = tags[i];
            long p = pointers[i];
            if ((t & qt) == qt) {
                /* per-iteration noinline call — loop-invariant arg but cannot be hoisted */
                matches += expensive_check_v287(qt) + (int)(p & 0xFF);
            }
        }
    }
    return matches;
}