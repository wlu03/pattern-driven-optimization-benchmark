typedef struct { int a, b; } Hot_v195;
int fast_comp_v195(Hot_v195 *h, int n) {
    int acc = 0;
    for (int i = 0; i < n; i++) {
        acc += h[i].a * h[i].b;
    }
    return acc;
}