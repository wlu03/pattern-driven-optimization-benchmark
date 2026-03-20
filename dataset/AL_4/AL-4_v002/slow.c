long long slow_al4_v002(int r,int c){
    if(r==0||c==0) return 1;
    return slow_al4_v002(r-1,c)+slow_al4_v002(r,c-1);
}