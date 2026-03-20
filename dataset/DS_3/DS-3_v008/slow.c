typedef struct{double data[32];int size;} BS_v008;

double slow_ds3_v008(BS_v008 s){double sum=0;for(int i=0;i<s.size;i++) sum+=s.data[i];return sum;}