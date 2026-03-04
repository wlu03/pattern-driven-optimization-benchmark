long long slow_al1_v044(int n) {
    if (n <= 1) return 1;
    long long res = 0;
    for (int i = 0; i < n; i++)
        res += slow_al1_v044(i) * slow_al1_v044(n - 1 - i);
    return res;
}