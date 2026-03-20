long long slow_al1_v011(int n) {
    if (n <= 0) return (n == 0) ? 1 : 0;
    return slow_al1_v011(n-1) + slow_al1_v011(n-2) + slow_al1_v011(n-3) + slow_al1_v011(n-4);
}