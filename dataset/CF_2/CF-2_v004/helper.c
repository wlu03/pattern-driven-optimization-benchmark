__attribute__((noinline, noclone))
int cf2_check_v004(int i, int j, int rows, int cols) {
    return (i * cols + j >= 0 && j >= 0 && j < cols && i * cols + j < rows * cols);
}