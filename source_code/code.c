#include <stdio.h>
#include <stdlib.h>
#include <limits.h>

unsigned long long hamming(int n) {
    int bases[] = {2, 3, 5};
    int expos[] = {0, 0, 0};
    unsigned long long *hamms = (unsigned long long*)malloc(n * sizeof(unsigned long long));
    hamms[0] = 1;

    for (int j = 1; j < n; j++)  {
        unsigned long long next_hamms[3];
        for (int i = 0; i < 3; i++) {
            next_hamms[i] = bases[i] * hamms[expos[i]];
        }
        unsigned long long next_hamm = ULLONG_MAX;
        for (int i = 0; i < 3; i++) {
            if (next_hamms[i] < next_hamm) next_hamm = next_hamms[i];
        }
        hamms[j] = next_hamm;

        for (int i = 0; i < 3; i++) expos[i] += (next_hamms[i] == next_hamm);
    }
    
    unsigned long long result = hamms[n - 1];
    free(hamms);
    return result;
}

int main() {
    int n = 12689;
    // The 12689th regular number is 9183300480000000000
    printf("The %dth regular number is %lld\n", n, hamming(n));
    return 0;
}