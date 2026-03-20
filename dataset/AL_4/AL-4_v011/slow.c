long long slow_al4_v011(int r,int c){
    if(r==0||c==0) return 1;
    return slow_al4_v011(r-1,c)+slow_al4_v011(r,c-1);
}