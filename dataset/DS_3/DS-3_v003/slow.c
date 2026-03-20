typedef struct{double data[64];int size;} BS_v003;

double slow_ds3_v003(BS_v003 s){double mx=s.data[0];for(int i=1;i<s.size;i++) if(s.data[i]>mx) mx=s.data[i];return mx;}