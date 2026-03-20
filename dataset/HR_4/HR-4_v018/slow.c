double hr4_check_v018(double *A, double *B, int idx, int n);

double slow_hr4_v018(double *A,double *B,int n){
    double sum=0;
    for(int i=0;i<n;i++) sum+=hr4_check_v018(A,B,i,n);
    return sum;
}