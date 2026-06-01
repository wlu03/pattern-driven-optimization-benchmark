typedef struct { float a, b; } Hot_v397;
float fast_comp_v397(Hot_v397 *h, int n) {
    float acc = 0;
    for (int i = 0; i < n; i++) {
        acc += h[i].a * h[i].b;
    }
    return acc;
}