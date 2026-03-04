long long slow_al1_v041(int r, int c) {
    if (r == 0 || c == 0) return 1;
    return slow_al1_v041(r-1, c) + slow_al1_v041(r, c-1);
}