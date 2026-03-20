double hr4_check_v008(double *A, double *B, int idx, int n);

double slow_hr4_v008(double *A,double *B,int n){
    double sum=0;
    for(int i=0;i<n;i++) sum+=hr4_check_v008(A,B,i,n);
    return sum;
}