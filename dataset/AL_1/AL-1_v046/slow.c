long long slow_al1_v046(int n, int k) {
    if (k == 0 || k == n) return 1;
    return slow_al1_v046(n-1, k-1) + slow_al1_v046(n-1, k);
}