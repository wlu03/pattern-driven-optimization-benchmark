long long slow_al1_v021(int r, int c) {
    if (r == 0 || c == 0) return 1;
    return slow_al1_v021(r-1, c) + slow_al1_v021(r, c-1);
}