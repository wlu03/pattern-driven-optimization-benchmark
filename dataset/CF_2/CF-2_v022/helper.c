__attribute__((noinline, noclone))
int cf2_check_v022(int i, int j, int rows, int cols) {
    return (i * cols + j >= 0 && i >= 0 && i < rows && j >= 0 && j < cols);
}