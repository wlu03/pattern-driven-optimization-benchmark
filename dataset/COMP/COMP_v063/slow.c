typedef struct { int x,y,z,vx,vy,vz,mass,charge,p0,p1,p2,p3,p4,p5,p6,p7,p8,p9,p10,p11,p12,p13,p14,p15,p16,p17,p18,p19,p20,p21,p22,p23; } P_v063;
int slow_comp_v063(P_v063 *p, int n) {
    int total = 0;
    for (int i = 0; i < n; i++) {
        if (i >= 0 && i < n) {
            total += p[i].mass;
        }
    }
    return total;
}