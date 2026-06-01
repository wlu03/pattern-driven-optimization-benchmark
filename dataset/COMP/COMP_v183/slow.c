typedef struct { float a, b, cold0,cold1,cold2,cold3,cold4,cold5,cold6,cold7,cold8,cold9,cold10,cold11,cold12,cold13,cold14,cold15,cold16,cold17,cold18,cold19,cold20,cold21,cold22,cold23,cold24,cold25,cold26,cold27,cold28,cold29; } Wide_v183;
float slow_comp_v183(Wide_v183 *w, int n) {
    float acc = 0;
    for (int i = 0; i < n; i++) {
        acc += w[i].a * w[i].b;
    }
    return acc;
}