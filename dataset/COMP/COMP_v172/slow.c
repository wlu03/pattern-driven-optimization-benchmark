static __attribute__((noinline)) double apply_v172(double x, int mode){
    volatile int _m=mode; /* block ipa-pure-const inference */
    if (_m==1) return x*(double)2.0;
    else if (_m==2) return x+(double)1.0;
    else return x-(double)0.5;
}
void slow_comp_v172(double *mat, int rows, int cols, int mode) {
    for (int j = 0; j < cols; j++) {
        for (int i = 0; i < rows; i++) {
            mat[i * cols + j] = apply_v172(mat[i * cols + j], mode);
        }
    }
}