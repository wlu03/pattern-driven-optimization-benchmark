long long slow_al1_v033(int n) {
    if (n <= 0) return (n == 0) ? 1 : 0;
    return slow_al1_v033(n-1) + slow_al1_v033(n-2) + slow_al1_v033(n-3) + slow_al1_v033(n-4);
}