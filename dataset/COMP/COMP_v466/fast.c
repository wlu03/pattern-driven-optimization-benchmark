typedef struct { int a, b; } Hot_v466;
int fast_comp_v466(Hot_v466 *h, int n) {
    int acc = 0;
    for (int i = 0; i < n; i++) {
        acc += h[i].a * h[i].b;
    }
    return acc;
}