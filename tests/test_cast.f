PROGRAM TESTCAST
INTEGER N, CASTN
REAL X, CASTX
N = 42
X = 3.14
CASTN = INT(X)
CASTX = REAL(N)
PRINT *, 'Float 3.14 para Int (deve ser 3): ', CASTN
PRINT *, 'Int 42 para Float (deve ser 42.0): ', CASTX
END