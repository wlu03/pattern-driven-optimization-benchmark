long long slow_al1_v001(int n) {
    if (n == 0) return 0;
    if (n <= 2) return 1;
    return slow_al1_v001(n-1) + slow_al1_v001(n-2) + slow_al1_v001(n-3);
}