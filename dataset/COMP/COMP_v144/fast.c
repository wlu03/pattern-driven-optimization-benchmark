typedef struct { int a, b; } Hot_v144;
int fast_comp_v144(Hot_v144 *h, int n) {
    int acc = 0;
    for (int i = 0; i < n; i++) {
        acc += h[i].a * h[i].b;
    }
    return acc;
}