__attribute__((noinline, noclone))
int cf2_check_v021(int i, int j, int rows, int cols) {
    return (j >= 0 && j < cols && i * cols + j < rows * cols);
}