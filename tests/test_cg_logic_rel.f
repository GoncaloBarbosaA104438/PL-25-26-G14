PROGRAM TESTLOGIC
INTEGER X, Y
LOGICAL RES
X = 10
Y = 20
RES = (X .LT. Y) .AND. .NOT. (X .EQ. Y)
IF (RES .OR. .FALSE.) THEN
    PRINT *, 'Logica e Relacionais funcionam perfeitamente!'
ELSE
    PRINT *, 'ERRO: A logica falhou.'
ENDIF
END