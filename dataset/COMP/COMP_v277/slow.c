static __attribute__((noinline)) float expensive_lookup_v277(int key){
    volatile int _k=key; /* block ipa-pure-const */
    float r=0;
    for(int i=1;i<=80;i++) r+=(float)sin((double)(_k+i)*0.1);
    return r;
}
static __attribute__((noinline)) long fib_rec_v277(int n){
    if (n < 2) return n;
    return fib_rec_v277(n-1) + fib_rec_v277(n-2);
}
float slow_comp_v277(int n_iters, int fib_k, int key) {
    float acc = 0;
    for (int i = 0; i < n_iters; i++) {
        float seed = expensive_lookup_v277(key);
        long f = fib_rec_v277(fib_k);
        acc += seed + (float)f;
    }
    return acc;
}