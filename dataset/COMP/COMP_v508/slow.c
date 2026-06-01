static __attribute__((noinline)) int expensive_lookup_v508(int key){
    volatile int _k=key; /* block ipa-pure-const */
    int r=0;
    for(int i=1;i<=80;i++) r+=(int)sin((double)(_k+i)*0.1);
    return r;
}
static __attribute__((noinline)) long fib_rec_v508(int n){
    if (n < 2) return n;
    return fib_rec_v508(n-1) + fib_rec_v508(n-2);
}
int slow_comp_v508(int n_iters, int fib_k, int key) {
    int acc = 0;
    for (int i = 0; i < n_iters; i++) {
        int seed = expensive_lookup_v508(key);
        long f = fib_rec_v508(fib_k);
        acc += seed + (int)f;
    }
    return acc;
}