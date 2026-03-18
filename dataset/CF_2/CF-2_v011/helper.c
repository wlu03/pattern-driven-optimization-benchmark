__attribute__((noinline, noclone))
int cf2_check_v011(int i, int j, int rows, int cols) {
    return (i * cols + j < rows * cols && j >= 0 && j < cols);
}