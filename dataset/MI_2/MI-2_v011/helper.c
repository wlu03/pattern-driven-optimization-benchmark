#include <string.h>

__attribute__((noinline))
void mi2_zero_v011(void *p, int n){
    volatile char *vp = (volatile char*)p;
    memset((void*)vp, 0, n);
}
