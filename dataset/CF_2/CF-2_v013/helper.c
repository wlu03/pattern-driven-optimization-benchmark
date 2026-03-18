__attribute__((noinline, noclone))
int cf2_check_v013(int i, int j, int rows, int cols) {
    return (i * cols + j >= 0 && j >= 0 && j < cols);
}