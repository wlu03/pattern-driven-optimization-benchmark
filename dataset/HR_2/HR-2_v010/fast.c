void fast_hr2_v010(float *X,float *Y,int n,
    float *mx,float *my,float *vx,float *vy){
    float sx=0,sy=0;
    for(int i=0;i<n;i++){sx+=X[i];sy+=Y[i];}
    *mx=sx/n; *my=sy/n;
    float mvx=*mx,mvy=*my,vsx=0,vsy=0;
    for(int i=0;i<n;i++){float dx=X[i]-mvx,dy=Y[i]-mvy;vsx+=dx*dx;vsy+=dy*dy;}
    *vx=vsx/n; *vy=vsy/n;
}