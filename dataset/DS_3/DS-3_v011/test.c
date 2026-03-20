#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#define N_FIELDS 32
#define N_STRUCTS 1000000
typedef struct{double f0;double f1;double f2;double f3;double f4;double f5;double f6;double f7;double f8;double f9;double f10;double f11;double f12;double f13;double f14;double f15;double f16;double f17;double f18;double f19;double f20;double f21;double f22;double f23;double f24;double f25;double f26;double f27;double f28;double f29;double f30;double f31;} BS_v011;

// SLOW_CODE_HERE

// FAST_CODE_HERE

int main() {
    BS_v011 *arr=(BS_v011*)malloc(N_STRUCTS*sizeof(BS_v011));
    for(int i=0;i<N_STRUCTS;i++){arr[i].f0=(double)((i+0)%100)*0.01;arr[i].f1=(double)((i+1)%100)*0.01;arr[i].f2=(double)((i+2)%100)*0.01;arr[i].f3=(double)((i+3)%100)*0.01;arr[i].f4=(double)((i+4)%100)*0.01;arr[i].f5=(double)((i+5)%100)*0.01;arr[i].f6=(double)((i+6)%100)*0.01;arr[i].f7=(double)((i+7)%100)*0.01;arr[i].f8=(double)((i+8)%100)*0.01;arr[i].f9=(double)((i+9)%100)*0.01;arr[i].f10=(double)((i+10)%100)*0.01;arr[i].f11=(double)((i+11)%100)*0.01;arr[i].f12=(double)((i+12)%100)*0.01;arr[i].f13=(double)((i+13)%100)*0.01;arr[i].f14=(double)((i+14)%100)*0.01;arr[i].f15=(double)((i+15)%100)*0.01;arr[i].f16=(double)((i+16)%100)*0.01;arr[i].f17=(double)((i+17)%100)*0.01;arr[i].f18=(double)((i+18)%100)*0.01;arr[i].f19=(double)((i+19)%100)*0.01;arr[i].f20=(double)((i+20)%100)*0.01;arr[i].f21=(double)((i+21)%100)*0.01;arr[i].f22=(double)((i+22)%100)*0.01;arr[i].f23=(double)((i+23)%100)*0.01;arr[i].f24=(double)((i+24)%100)*0.01;arr[i].f25=(double)((i+25)%100)*0.01;arr[i].f26=(double)((i+26)%100)*0.01;arr[i].f27=(double)((i+27)%100)*0.01;arr[i].f28=(double)((i+28)%100)*0.01;arr[i].f29=(double)((i+29)%100)*0.01;arr[i].f30=(double)((i+30)%100)*0.01;arr[i].f31=(double)((i+31)%100)*0.01;}
    struct timespec t0,t1;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    double rs=slow_ds3_v011(arr,N_STRUCTS);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_slow=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    clock_gettime(CLOCK_MONOTONIC,&t0);
    double rf=fast_ds3_v011(arr,N_STRUCTS);
    clock_gettime(CLOCK_MONOTONIC,&t1);
    double ms_fast=(t1.tv_sec-t0.tv_sec)*1000.0+(t1.tv_nsec-t0.tv_nsec)/1e6;
    double diff=fabs(rs-rf),ref=fabs(rs)+1e-12;
    int correct=diff<1e-6*ref;
    printf("slow_ms=%.4f fast_ms=%.4f correct=%d speedup=%.2f\n",ms_slow,ms_fast,correct,ms_slow/fmax(ms_fast,0.001));
    free(arr);return correct?0:1;
}