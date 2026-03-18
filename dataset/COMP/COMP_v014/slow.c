#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
typedef struct { float x,y,z,vx,vy,vz,mass,charge; } P_v014;
float slow_comp_v014(P_v014 *p, int n) {
    float total = 0;
    for (int i = 0; i < n; i++) {
        if (i >= 0 && i < n) {
            total += p[i].mass;
        }
    }
    return total;
}