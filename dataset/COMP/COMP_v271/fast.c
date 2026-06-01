static __attribute__((noinline)) double expensive_lookup_v271(int key){
    volatile int _k=key; /* block ipa-pure-const */
    double r=0;
    for(int i=1;i<=80;i++) r+=(double)sin((double)(_k+i)*0.1);
    return r;
}
static __attribute__((noinline)) long fib_rec_v271(int n){
    if (n < 2) return n;
    return fib_rec_v271(n-1) + fib_rec_v271(n-2);
}
double fast_comp_v271(int n_iters, int fib_k, int key) {
    double seed = expensive_lookup_v271(key);
    long a = 0, b = 1;
    for (int j = 0; j < fib_k; j++) { long t = a + b; a = b; b = t; }
    long f = a;
    return (double)n_iters * (seed + (double)f);
}