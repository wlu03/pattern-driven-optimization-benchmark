typedef struct { double a, b; } Hot_v485;
double fast_comp_v485(Hot_v485 *h, int n) {
    double acc = 0;
    for (int i = 0; i < n; i++) {
        acc += h[i].a * h[i].b;
    }
    return acc;
}