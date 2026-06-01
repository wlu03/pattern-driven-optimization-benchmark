static __attribute__((noinline)) double expensive_lookup_v611(int key){
    volatile int _k=key; /* block ipa-pure-const */
    double r=0;
    for(int i=1;i<=80;i++) r+=(double)sin((double)(_k+i)*0.1);
    return r;
}
static __attribute__((noinline)) long fib_rec_v611(int n){
    if (n < 2) return n;
    return fib_rec_v611(n-1) + fib_rec_v611(n-2);
}
double slow_comp_v611(int n_iters, int fib_k, int key) {
    double acc = 0;
    for (int i = 0; i < n_iters; i++) {
        double seed = expensive_lookup_v611(key);
        long f = fib_rec_v611(fib_k);
        acc += seed + (double)f;
    }
    return acc;
}