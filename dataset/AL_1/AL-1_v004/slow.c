long long slow_al1_v004(int n) {
    if (n == 0) return 1;
    if (n == 1) return 0;
    return (n - 1) * (slow_al1_v004(n - 1) + slow_al1_v004(n - 2));
}