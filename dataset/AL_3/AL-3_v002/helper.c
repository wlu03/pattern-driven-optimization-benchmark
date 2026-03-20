__attribute__((noinline))
int al3_cmp_v002(int a, int b){
    volatile int va = a, vb = b;
    return va == vb;
}
