typedef struct{double data[64];int size;} BS_v004;

double fast_ds3_v004(const BS_v004 *s){double sum=0;for(int i=0;i<s->size;i++) sum+=s->data[i];return sum;}