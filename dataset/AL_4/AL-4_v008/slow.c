long long slow_al4_v008(int r,int c){
    if(r==0||c==0) return 1;
    return slow_al4_v008(r-1,c)+slow_al4_v008(r,c-1);
}