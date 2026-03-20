typedef struct{double data[128];int size;} BS_v012;

double fast_ds3_v012(const BS_v012 *s){double mx=s->data[0];for(int i=1;i<s->size;i++) if(s->data[i]>mx) mx=s->data[i];return mx;}