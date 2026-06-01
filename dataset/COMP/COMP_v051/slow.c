static __attribute__((noinline)) float apply_v051(float x, int mode){
    volatile int _m=mode; /* block ipa-pure-const inference */
    if (_m==1) return x*(float)2.0;
    else if (_m==2) return x+(float)1.0;
    else return x-(float)0.5;
}
void slow_comp_v051(float *mat, int rows, int cols, int mode) {
    for (int j = 0; j < cols; j++) {
        for (int i = 0; i < rows; i++) {
            mat[i * cols + j] = apply_v051(mat[i * cols + j], mode);
        }
    }
}