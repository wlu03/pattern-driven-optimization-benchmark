typedef struct { double a, b; } Hot_v387;
double fast_comp_v387(Hot_v387 *h, int n) {
    double acc = 0;
    for (int i = 0; i < n; i++) {
        acc += h[i].a * h[i].b;
    }
    return acc;
}