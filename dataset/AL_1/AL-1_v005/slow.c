long long slow_al1_v005(int n) {
    if (n == 0) return 0;
    if (n <= 2) return 1;
    return slow_al1_v005(n-1) + slow_al1_v005(n-2) + slow_al1_v005(n-3);
}