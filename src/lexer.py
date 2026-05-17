import ply.lex as lex


reserved = {
    "PROGRAM": "PROGRAM",
    "END": "END",
    "INTEGER": "INTEGER",
    "REAL": "REAL",
    "LOGICAL": "LOGICAL",
    "IF": "IF",
    "THEN": "THEN",
    "ELSE": "ELSE",
    "ENDIF": "ENDIF",
    "DO": "DO",
    "CONTINUE": "CONTINUE",
    "GOTO": "GOTO",
    "PRINT": "PRINT",
    "READ": "READ",
}


tokens = [
    *reserved.values(),
    "ID",
    "INTEGER_LITERAL",
    "REAL_LITERAL",
    "STRING_LITERAL",
    "PLUS",
    "MINUS",
    "TIMES",
    "DIVIDE",
    "ASSIGN",
    "LPAREN",
    "RPAREN",
    "COMMA",
    "EQ",
    "NE",
    "LT",
    "LE",
    "GT",
    "GE",
    "TRUE",
    "FALSE",
    "AND",
    "OR",
    "NOT",
]


t_PLUS = r"\+"
t_MINUS = r"-"
t_TIMES = r"\*"
t_DIVIDE = r"/"
t_ASSIGN = r"="
t_LPAREN = r"\("
t_RPAREN = r"\)"
t_COMMA = r","

t_EQ = r"\.EQ\."
t_NE = r"\.NE\."
t_LT = r"\.LT\."
t_LE = r"\.LE\."
t_GT = r"\.GT\."
t_GE = r"\.GE\."
t_TRUE = r"\.TRUE\."
t_FALSE = r"\.FALSE\."
t_AND = r"\.AND\."
t_OR = r"\.OR\."
t_NOT = r"\.NOT\."

t_ignore = " \t"


def t_REAL_LITERAL(t):
    r"(\d+\.\d*|\.\d+)"
    t.value = float(t.value)
    return t


def t_INTEGER_LITERAL(t):
    r"\d+"
    t.value = int(t.value)
    return t


def t_STRING_LITERAL(t):
    r"'([^'\n]|'')*'"
    t.value = t.value[1:-1].replace("''", "'")
    return t


def t_ID(t):
    r"[A-Za-z][A-Za-z0-9]*"
    value = t.value.upper()
    t.type = reserved.get(value, "ID")
    t.value = value
    return t


def t_newline(t):
    r"\n+"
    t.lexer.lineno += len(t.value)


def t_error(t):
    print(f"Illegal character {t.value[0]!r} at line {t.lexer.lineno}")
    t.lexer.skip(1)


lexer = lex.lex()