static __attribute__((noinline)) int apply_v360(int x, int mode){
    volatile int _m=mode; /* block ipa-pure-const inference */
    if (_m==1) return x*(int)2.0;
    else if (_m==2) return x+(int)1.0;
    else return x-(int)0.5;
}
void slow_comp_v360(int *mat, int rows, int cols, int mode) {
    for (int j = 0; j < cols; j++) {
        for (int i = 0; i < rows; i++) {
            mat[i * cols + j] = apply_v360(mat[i * cols + j], mode);
        }
    }
}