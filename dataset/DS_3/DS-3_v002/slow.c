typedef struct{double data[32];int size;} BS_v002;

double slow_ds3_v002(BS_v002 s){double sum=0;for(int i=0;i<s.size;i++) sum+=s.data[i]*s.data[i];return sum;}