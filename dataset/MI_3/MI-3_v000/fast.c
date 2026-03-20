double fast_mi3_v000(double *data,int n){
    double total=0.0;
    for(int i=0;i<n-7;i++) total+=(data[i+0]+data[i+1]+data[i+2]+data[i+3]+data[i+4]+data[i+5]+data[i+6]+data[i+7])*0.5;
    return total;
}