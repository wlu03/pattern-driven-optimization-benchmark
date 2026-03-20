double fast_mi3_v008(double *data,int n){
    double total=0.0;
    for(int i=0;i<n-3;i++) total+=(data[i+0]+data[i+1]+data[i+2]+data[i+3])*0.125;
    return total;
}