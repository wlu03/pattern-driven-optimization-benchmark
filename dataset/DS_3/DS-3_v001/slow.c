typedef struct{double data[128];int size;} BS_v001;

double slow_ds3_v001(BS_v001 s){double sum=0;for(int i=0;i<s.size;i++) sum+=s.data[i];return sum;}