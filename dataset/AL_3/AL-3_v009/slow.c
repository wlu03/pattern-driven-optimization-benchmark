int al3_cmp_v009(int a, int b);

int slow_al3_v009(int *text,int tn,int *pat,int pn){
    int count=0;
    for(int i=0;i<=tn-pn;i++){
        int m=1;
        for(int j=0;j<pn;j++){
            if(!al3_cmp_v009(text[i+j],pat[j])){m=0;break;}
        }
        if(m) count++;
    }
    return count;
}
