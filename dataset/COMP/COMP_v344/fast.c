typedef struct { float a, b; } Hot_v344;
float fast_comp_v344(Hot_v344 *h, int n) {
    float acc = 0;
    for (int i = 0; i < n; i++) {
        acc += h[i].a * h[i].b;
    }
    return acc;
}