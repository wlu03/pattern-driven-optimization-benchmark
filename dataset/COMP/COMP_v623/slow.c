static long *_dp_table_v623 = 0;
static int _dp_cols_v623 = 0;
static __attribute__((noinline)) long dp_descent_v623(int i, int j){
    if (i == 0 || j == 0) return 1;
    long *t = _dp_table_v623;
    int c = _dp_cols_v623;
    if (t[i*c+j] != 0) return t[i*c+j];
    long r = dp_descent_v623(i-1, j) + dp_descent_v623(i, j-1);
    t[i*c+j] = r;
    return r;
}
long slow_comp_v623(int rows, int cols) {
    long *table = (long*)calloc((size_t)rows * cols, sizeof(long));
    _dp_table_v623 = table;
    _dp_cols_v623 = cols;
    long acc = 0;
    /* column-major outer order — fills col-by-col into row-major-stored table */
    for (int j = 0; j < cols; j++) {
        for (int i = 0; i < rows; i++) {
            acc += dp_descent_v623(i, j);
        }
    }
    free(table);
    _dp_table_v623 = 0;
    return acc;
}