void slow_hr2_v013(double *X,double *Y,int n,
    double *mx,double *my,double *vx,double *vy){
    double sx=0;
    for(int i=0;i<n;i++) sx+=X[i];
    *mx=sx/n;
    asm volatile("" ::: "memory");
    double sy=0;
    for(int i=0;i<n;i++) sy+=Y[i];
    *my=sy/n;
    asm volatile("" ::: "memory");
    double vs=0;
    for(int i=0;i<n;i++){double d=X[i]-*mx;vs+=d*d;}
    *vx=vs/n;
    asm volatile("" ::: "memory");
    double vy2=0;
    for(int i=0;i<n;i++){double d=Y[i]-*my;vy2+=d*d;}
    *vy=vy2/n;
}