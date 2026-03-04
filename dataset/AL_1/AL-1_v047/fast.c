long long fast_al1_v047(int n) {
    if (n <= 1) return n;
    long long a = 0, b = 1;
    for (int i = 2; i <= n; i++) { long long t = a+b; a = b; b = t; }
    return b;
}