void slow_hr2_v009(float *X,float *Y,int n,
    float *mx,float *my,float *vx,float *vy){
    float sx=0;
    for(int i=0;i<n;i++) sx+=X[i];
    *mx=sx/n;
    float sy=0;
    for(int i=0;i<n;i++) sy+=Y[i];
    *my=sy/n;
    float vs=0;
    for(int i=0;i<n;i++){float d=X[i]-*mx;vs+=d*d;}
    *vx=vs/n;
    float vy2=0;
    for(int i=0;i<n;i++){float d=Y[i]-*my;vy2+=d*d;}
    *vy=vy2/n;
}