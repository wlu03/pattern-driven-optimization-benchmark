static __attribute__((noinline)) float expensive_lookup_v203(int key){
    volatile int _k=key; /* block ipa-pure-const */
    float r=0;
    for(int i=1;i<=80;i++) r+=(float)sin((double)(_k+i)*0.1);
    return r;
}
static __attribute__((noinline)) long fib_rec_v203(int n){
    if (n < 2) return n;
    return fib_rec_v203(n-1) + fib_rec_v203(n-2);
}
float fast_comp_v203(int n_iters, int fib_k, int key) {
    float seed = expensive_lookup_v203(key);
    long a = 0, b = 1;
    for (int j = 0; j < fib_k; j++) { long t = a + b; a = b; b = t; }
    long f = a;
    return (float)n_iters * (seed + (float)f);
}