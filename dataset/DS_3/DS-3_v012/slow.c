typedef struct{double f0;double f1;double f2;double f3;double f4;double f5;double f6;double f7;double f8;double f9;double f10;double f11;double f12;double f13;double f14;double f15;double f16;double f17;double f18;double f19;double f20;double f21;double f22;double f23;double f24;double f25;double f26;double f27;double f28;double f29;double f30;double f31;} BS_v012;
double ds3_process_v012(BS_v012 s);

double slow_ds3_v012(BS_v012 *arr, int n){
    double total=0.0;
    for(int i=0;i<n;i++) total+=ds3_process_v012(arr[i]);
    return total;
}
