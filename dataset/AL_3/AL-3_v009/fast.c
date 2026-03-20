static void build_fail_v009(int *pat,int pn,int *fail){
    fail[0]=0; int k=0;
    for(int i=1;i<pn;i++){
        while(k>0&&pat[k]!=pat[i]) k=fail[k-1];
        if(pat[k]==pat[i]) k++;
        fail[i]=k;
    }
}

int fast_al3_v009(int *text,int tn,int *pat,int pn){
    int *fail=(int*)malloc(pn*sizeof(int));
    build_fail_v009(pat,pn,fail);
    int count=0,k=0;
    for(int i=0;i<tn;i++){
        while(k>0&&pat[k]!=text[i]) k=fail[k-1];
        if(pat[k]==text[i]) k++;
        if(k==pn){count++;k=fail[k-1];}
    }
    free(fail);
    return count;
}