#include <stdlib.h>

__attribute__((noinline))
void* ds2_alloc_v006(int n){
    volatile void *p = malloc(n);
    return (void*)p;
}

__attribute__((noinline))
void ds2_free_v006(void *p){
    volatile void *vp = p;
    free((void*)vp);
}
