typedef struct{double data[32];int size;} BS_v013;

double slow_ds3_v013(BS_v013 s){double mx=s.data[0];for(int i=1;i<s.size;i++) if(s.data[i]>mx) mx=s.data[i];return mx;}