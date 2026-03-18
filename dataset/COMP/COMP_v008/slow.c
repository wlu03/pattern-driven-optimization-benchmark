#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

__attribute__((noinline))
typedef struct { int x,y,z,vx,vy,vz,mass,charge; } P_v008;
int slow_comp_v008(P_v008 *p, int n) {
    int total = 0;
    for (int i = 0; i < n; i++) {
        if (i >= 0 && i < n) {
            total += p[i].mass;
        }
    }
    return total;
}