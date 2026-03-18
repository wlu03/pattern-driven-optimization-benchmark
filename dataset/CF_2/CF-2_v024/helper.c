__attribute__((noinline, noclone))
int cf2_check_v024(int i, int j, int rows, int cols) {
    return (i * cols + j < rows * cols && i >= 0 && i < rows);
}