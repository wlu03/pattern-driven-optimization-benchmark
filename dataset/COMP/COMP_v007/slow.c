typedef struct { double x,y,z,vx,vy,vz,mass,charge; } P_v007;
double slow_comp_v007(P_v007 *p, int n) {
    double total = 0.0;
    for (int i = 0; i < n; i++) {
        // Pattern CF-2: Redundant bounds check
        if (i >= 0 && i < n) {
            // Pattern DS-4: AoS access for single field
            total += p[i].mass;
        }
    }
    return total;
}