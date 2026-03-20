typedef struct{double data[64];int size;} BS_v006;

double slow_ds3_v006(BS_v006 s){double sum=0;for(int i=0;i<s.size;i++) sum+=s.data[i];return sum;}