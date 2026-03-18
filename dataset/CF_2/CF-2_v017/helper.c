__attribute__((noinline, noclone))
int cf2_check_v017(int i, int j, int rows, int cols) {
    return (j >= 0 && j < cols && i >= 0 && i < rows && i * cols + j >= 0);
}