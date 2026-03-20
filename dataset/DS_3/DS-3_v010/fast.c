typedef struct{double data[64];int size;} BS_v010;

double fast_ds3_v010(const BS_v010 *s){double mx=s->data[0];for(int i=1;i<s->size;i++) if(s->data[i]>mx) mx=s->data[i];return mx;}