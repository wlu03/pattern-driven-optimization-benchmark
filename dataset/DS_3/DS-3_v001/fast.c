typedef struct{double data[128];int size;} BS_v001;

double fast_ds3_v001(const BS_v001 *s){double sum=0;for(int i=0;i<s->size;i++) sum+=s->data[i];return sum;}