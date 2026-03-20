int slow_al1_v000(int n, int max_val) {
    if (n == 0) return 1;
    if (n < 0 || max_val == 0) return 0;
    return slow_al1_v000(n - max_val, max_val) + slow_al1_v000(n, max_val - 1);
}