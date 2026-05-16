PROGRAM TESTARR
INTEGER NUMS(5)
INTEGER I
PRINT *, 'Teste de Arrays e MOD:'
DO 10 I = 1, 5
    NUMS(I) = MOD(I * 3, 4)
    PRINT *, 'Indice ', I, ' tem o valor (MOD 4): ', NUMS(I)
10 CONTINUE
END