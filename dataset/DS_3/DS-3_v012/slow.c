typedef struct{double data[128];int size;} BS_v012;

double slow_ds3_v012(BS_v012 s){double mx=s.data[0];for(int i=1;i<s.size;i++) if(s.data[i]>mx) mx=s.data[i];return mx;}