__attribute__((noinline, noclone))
int cf2_check_v002(int i, int j, int rows, int cols) {
    return (i * cols + j < rows * cols && i * cols + j >= 0);
}