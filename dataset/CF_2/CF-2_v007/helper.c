__attribute__((noinline, noclone))
int cf2_check_v007(int i, int j, int rows, int cols) {
    return (i >= 0 && i < rows && i * cols + j >= 0);
}