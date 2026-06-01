typedef struct{double f0;double f1;double f2;double f3;double f4;double f5;double f6;double f7;double f8;double f9;double f10;double f11;double f12;double f13;double f14;double f15;double f16;double f17;double f18;double f19;double f20;double f21;double f22;double f23;double f24;double f25;double f26;double f27;double f28;double f29;double f30;double f31;double f32;double f33;double f34;double f35;double f36;double f37;double f38;double f39;double f40;double f41;double f42;double f43;double f44;double f45;double f46;double f47;double f48;double f49;double f50;double f51;double f52;double f53;double f54;double f55;double f56;double f57;double f58;double f59;double f60;double f61;double f62;double f63;double f64;double f65;double f66;double f67;double f68;double f69;double f70;double f71;double f72;double f73;double f74;double f75;double f76;double f77;double f78;double f79;double f80;double f81;double f82;double f83;double f84;double f85;double f86;double f87;double f88;double f89;double f90;double f91;double f92;double f93;double f94;double f95;} BS_v003;
double ds3_process_v003(BS_v003 s);

double slow_ds3_v003(BS_v003 *arr, int n){
    double total=0.0;
    for(int i=0;i<n;i++) total+=ds3_process_v003(arr[i]);
    return total;
}
