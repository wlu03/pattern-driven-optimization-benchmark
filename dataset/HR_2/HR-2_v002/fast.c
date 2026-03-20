void fast_hr2_v002(double *X,double *Y,int n,
    double *mx,double *my,double *vx,double *vy){
    double sx=0,sy=0;
    for(int i=0;i<n;i++){sx+=X[i];sy+=Y[i];}
    *mx=sx/n; *my=sy/n;
    double mvx=*mx,mvy=*my,vsx=0,vsy=0;
    for(int i=0;i<n;i++){double dx=X[i]-mvx,dy=Y[i]-mvy;vsx+=dx*dx;vsy+=dy*dy;}
    *vx=vsx/n; *vy=vsy/n;
}