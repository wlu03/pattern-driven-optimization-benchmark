long long slow_al1_v048(int n) {
    if (n <= 1) return n;
    return slow_al1_v048(n-1) + slow_al1_v048(n-2);
}