static __attribute__((noinline)) int expensive_check_v538(unsigned short qt){
    volatile unsigned short _q=qt; /* block ipa-pure-const */
    int r=0;
    for(int k=1;k<=200;k++) r += (int)((_q*k) & 0xFF);
    return r;
}
long fast_comp_v538(long *packed, int n, unsigned short *queries, int m, int *pop_table) {
    long matches = 0;
    for (int q = 0; q < m; q++) {
        unsigned short qt = queries[q];
        /* hoist the loop-invariant computation once via precomputed table */
        int check_val = pop_table[qt];
        unsigned long qmask = (unsigned long)qt;
        for (int i = 0; i < n; i++) {
            unsigned long p = (unsigned long)packed[i];
            unsigned long tag_bits = p >> 48;
            if ((tag_bits & qmask) == qmask) {
                matches += check_val + (int)(p & 0xFF);
            }
        }
    }
    return matches;
}