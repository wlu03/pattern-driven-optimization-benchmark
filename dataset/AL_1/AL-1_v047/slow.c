long long slow_al1_v047(int n) {
    if (n <= 1) return n;
    return slow_al1_v047(n-1) + slow_al1_v047(n-2);
}