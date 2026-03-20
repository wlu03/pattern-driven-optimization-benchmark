#include <stdlib.h>

__attribute__((noinline))
void* mi3_alloc_v005(int n){
    volatile void *p = malloc(n);
    return (void*)p;
}

__attribute__((noinline))
void mi3_free_v005(void *p){
    volatile void *vp = p;
    free((void*)vp);
}
