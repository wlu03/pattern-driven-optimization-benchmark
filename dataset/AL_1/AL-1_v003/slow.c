long long slow_al1_v003(int n) {
    if (n <= 1) return 1;
    long long res = 0;
    for (int i = 0; i < n; i++)
        res += slow_al1_v003(i) * slow_al1_v003(n - 1 - i);
    return res;
}