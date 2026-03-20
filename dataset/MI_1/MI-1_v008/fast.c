double fast_mi1_v008(double *input,int n,int window){
    double total=0.0,sum=0.0;
    for(int j=0;j<window;j++) sum+=input[j];
    total+=sum/window;
    for(int i=1;i<=n-window;i++){
        sum+=input[i+window-1]-input[i-1];
        total+=sum/window;
    }
    return total;
}