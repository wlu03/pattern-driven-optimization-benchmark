int slow_ds1_v008(int *keys,int *vals,int n_keys,int *queries,int n_q){
    int total=0;
    for(int q=0;q<n_q;q++){
        for(int i=0;i<n_keys;i++) if(keys[i]==queries[q]){total+=vals[i];break;}
    }
    return total;
}