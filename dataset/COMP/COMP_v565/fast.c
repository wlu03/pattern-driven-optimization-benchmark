static __attribute__((noinline)) int expensive_lookup_v565(int key){
    volatile int _k=key; /* block ipa-pure-const */
    int r=0;
    for(int i=1;i<=80;i++) r+=(int)sin((double)(_k+i)*0.1);
    return r;
}
static __attribute__((noinline)) long fib_rec_v565(int n){
    if (n < 2) return n;
    return fib_rec_v565(n-1) + fib_rec_v565(n-2);
}
int fast_comp_v565(int n_iters, int fib_k, int key) {
    int seed = expensive_lookup_v565(key);
    long a = 0, b = 1;
    for (int j = 0; j < fib_k; j++) { long t = a + b; a = b; b = t; }
    long f = a;
    return (int)n_iters * (seed + (int)f);
}