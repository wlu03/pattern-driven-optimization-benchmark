typedef struct{int key,val,occ;} HTE_v004;

int fast_ds1_v004(int *keys,int *vals,int n_keys,int *queries,int n_q){
    HTE_v004 *ht=(HTE_v004*)calloc(65536,sizeof(HTE_v004));
    for(int i=0;i<n_keys;i++){
        int h=(unsigned int)keys[i]&65535;
        while(ht[h].occ) h=(h+1)&65535;
        ht[h].key=keys[i];ht[h].val=vals[i];ht[h].occ=1;
    }
    int total=0;
    for(int q=0;q<n_q;q++){
        int h=(unsigned int)queries[q]&65535;
        while(ht[h].occ){if(ht[h].key==queries[q]){total+=ht[h].val;break;}h=(h+1)&65535;}
    }
    free(ht);
    return total;
}