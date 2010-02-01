%module libc

%{
#include <stdio.h>
%}

FILE *fopen(const char *, const char*);
int fread(void *, size_t, size_t, FILE *);
int fwrite(void *, size_t, size_t, FILE *);
int fclose(FILE *);
void *malloc(size_t);
