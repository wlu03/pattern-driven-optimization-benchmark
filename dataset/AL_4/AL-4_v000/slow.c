long long slow_al4_v000(int r,int c){
    if(r==0||c==0) return 1;
    return slow_al4_v000(r-1,c)+slow_al4_v000(r,c-1);
}