#include <stdlib.h>

__attribute__((noinline))
void* mi3_alloc_v013(int n){
    volatile void *p = malloc(n);
    return (void*)p;
}

__attribute__((noinline))
void mi3_free_v013(void *p){
    volatile void *vp = p;
    free((void*)vp);
}
