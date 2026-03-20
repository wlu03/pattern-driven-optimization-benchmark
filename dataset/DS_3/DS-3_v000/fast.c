typedef struct{double data[128];int size;} BS_v000;

double fast_ds3_v000(const BS_v000 *s){double sum=0;for(int i=0;i<s->size;i++) sum+=s->data[i]*s->data[i];return sum;}