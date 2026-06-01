typedef struct { float val, weight, p0,p1,p2,p3,p4,p5,p6,p7,p8,p9,p10,p11,p12,p13,p14,p15,p16,p17,p18,p19,p20,p21,p22,p23,p24,p25,p26,p27,p28,p29; } R_v516;
float slow_comp_v516(R_v516 *r, int n) {
    float acc = 0;
    for (int i = 0; i < n; i++) {
        acc += r[i].val * r[i].weight;
    }
    return acc;
}