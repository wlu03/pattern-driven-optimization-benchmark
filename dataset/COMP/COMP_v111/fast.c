typedef struct { float a, b; } Hot_v111;
float fast_comp_v111(Hot_v111 *h, int n) {
    float acc = 0;
    for (int i = 0; i < n; i++) {
        acc += h[i].a * h[i].b;
    }
    return acc;
}