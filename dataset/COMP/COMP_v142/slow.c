typedef struct { double a, b, cold0,cold1,cold2,cold3,cold4,cold5,cold6,cold7,cold8,cold9,cold10,cold11,cold12,cold13,cold14,cold15,cold16,cold17,cold18,cold19,cold20,cold21,cold22,cold23,cold24,cold25,cold26,cold27,cold28,cold29; } Wide_v142;
double slow_comp_v142(Wide_v142 *w, int n) {
    double acc = 0;
    for (int i = 0; i < n; i++) {
        acc += w[i].a * w[i].b;
    }
    return acc;
}