typedef struct { float a, b; } Hot_v384;
float fast_comp_v384(Hot_v384 *h, int n) {
    float acc = 0;
    for (int i = 0; i < n; i++) {
        acc += h[i].a * h[i].b;
    }
    return acc;
}