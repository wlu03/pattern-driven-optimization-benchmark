#include <stdlib.h>

__attribute__((noinline))
void* ds2_alloc_v000(int n){
    volatile void *p = malloc(n);
    return (void*)p;
}

__attribute__((noinline))
void ds2_free_v000(void *p){
    volatile void *vp = p;
    free((void*)vp);
}
