    PROGRAM TESTDO
    INTEGER I, SOMA
    SOMA = 0
    DO 10 I = 1, 5
        SOMA = SOMA + I
        IF (SOMA .GT. 10) THEN
            GOTO 20
        ENDIF
10  CONTINUE
20  PRINT *, 'Fim do ciclo. Soma:', SOMA
    END