#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N 2000000
typedef struct { int x,y,z,vx,vy,vz,mass,charge,p0,p1,p2,p3,p4,p5,p6,p7,p8,p9,p10,p11,p12,p13,p14,p15,p16,p17,p18,p19,p20,p21,p22,p23; } P_v063;

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    P_v063 *aos=(P_v063*)malloc(N*sizeof(P_v063));
    int *mass=malloc(N*sizeof(int));
    for(int i=0;i<N;i++){aos[i].mass=(int)(i%100)*0.1;mass[i]=aos[i].mass;}
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0); int rs=slow_comp_v063(aos,N); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0); int rf=fast_comp_v063(mass,N); clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    double diff=fabs((double)(rs-rf)),ref=fabs((double)rs)+1e-12;
    int correct=diff<1e-6*ref;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(aos);free(mass);return correct?0:1;
}