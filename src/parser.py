# pyright: ignore[reportShadowedImports]

"""Parser for the Fortran 77 compiler MVP."""

import ply.yacc as yacc

from src.ast_nodes import (
    Assign,
    BinOp,
    Continue,
    DoLoop,
    Goto,
    IfThenElse,
    LogicalConst,
    Num,
    Print,
    Program,
    Read,
    String,
    UnaryOp,
    Var,
    VarDecl,
)
from src.lexer import lexer, tokens


precedence = (
    ("left", "OR"),
    ("left", "AND"),
    ("right", "NOT"),
    ("nonassoc", "EQ", "NE", "LT", "LE", "GT", "GE"),
    ("left", "PLUS", "MINUS"),
    ("left", "TIMES", "DIVIDE"),
    ("right", "UMINUS"),
)


def set_label(statement, label_id):
    statement.label_id = label_id
    return statement


def expr_to_text(expr):
    if isinstance(expr, Var):
        return expr.name
    if isinstance(expr, Num):
        return str(expr.value)
    if isinstance(expr, String):
        return repr(expr.value)
    if isinstance(expr, LogicalConst):
        return ".TRUE." if expr.value else ".FALSE."
    return repr(expr)


def p_program(p):
    "program : PROGRAM ID declarations statement_list END"
    p[0] = Program(p[2], p[3], p[4])


def p_declarations_many(p):
    "declarations : declarations declaration"
    p[0] = p[1] + [p[2]]


def p_declarations_empty(p):
    "declarations :"
    p[0] = []


def p_declaration(p):
    "declaration : type_spec declarator_list"
    p[0] = VarDecl(p[1], p[2])


def p_type_spec(p):
    """type_spec : INTEGER
                 | REAL
                 | LOGICAL"""
    p[0] = p[1]


def p_declarator_list_many(p):
    "declarator_list : declarator_list COMMA declarator"
    p[0] = p[1] + [p[3]]


def p_declarator_list_one(p):
    "declarator_list : declarator"
    p[0] = [p[1]]


def p_declarator_id(p):
    "declarator : ID"
    p[0] = p[1]


def p_declarator_array(p):
    "declarator : ID LPAREN expression RPAREN"
    p[0] = f"{p[1]}({expr_to_text(p[3])})"


def p_statement_list_many(p):
    "statement_list : statement_list statement"
    p[0] = p[1] + [p[2]]


def p_statement_list_empty(p):
    "statement_list :"
    p[0] = []


def p_statement(p):
    "statement : optional_label statement_body"
    p[0] = set_label(p[2], p[1])


def p_do_statement_list_many(p):
    "do_statement_list : do_statement_list do_statement"
    p[0] = p[1] + [p[2]]


def p_do_statement_list_empty(p):
    "do_statement_list :"
    p[0] = []


def p_do_statement(p):
    "do_statement : optional_label do_statement_body"
    p[0] = set_label(p[2], p[1])


def p_optional_label(p):
    """optional_label : INTEGER_LITERAL
                      | empty"""
    p[0] = p[1]


def p_empty(p):
    "empty :"
    p[0] = None


def p_statement_body(p):
    """statement_body : assign_statement
                      | print_statement
                      | read_statement
                      | if_statement
                      | do_loop_statement
                      | goto_statement
                      | continue_statement"""
    p[0] = p[1]


def p_do_statement_body(p):
    """do_statement_body : assign_statement
                         | print_statement
                         | read_statement
                         | if_statement
                         | do_loop_statement
                         | goto_statement"""
    p[0] = p[1]


def p_assign_statement(p):
    "assign_statement : variable_ref ASSIGN expression"
    p[0] = Assign(p[1], p[3])


def p_print_statement(p):
    "print_statement : PRINT TIMES COMMA expression_list"
    p[0] = Print(p[4])


def p_read_statement(p):
    "read_statement : READ TIMES COMMA target_list"
    p[0] = Read(p[4])


def p_if_statement(p):
    "if_statement : IF LPAREN expression RPAREN THEN statement_list else_part ENDIF"
    p[0] = IfThenElse(p[3], p[6], p[7])


def p_else_part(p):
    """else_part : ELSE statement_list
                 | empty"""
    p[0] = p[2] if len(p) == 3 else []


def p_do_loop_statement(p):
    "do_loop_statement : DO INTEGER_LITERAL ID ASSIGN expression COMMA expression do_statement_list INTEGER_LITERAL CONTINUE"
    p[0] = DoLoop(p[2], p[3], p[5], p[7], p[8] + [Continue(label_id=p[9])])


def p_goto_statement(p):
    "goto_statement : GOTO INTEGER_LITERAL"
    p[0] = Goto(p[2])


def p_continue_statement(p):
    "continue_statement : CONTINUE"
    p[0] = Continue()


def p_target_list_many(p):
    "target_list : target_list COMMA variable_ref"
    p[0] = p[1] + [p[3]]


def p_target_list_one(p):
    "target_list : variable_ref"
    p[0] = [p[1]]


def p_expression_list_many(p):
    "expression_list : expression_list COMMA expression"
    p[0] = p[1] + [p[3]]


def p_expression_list_one(p):
    "expression_list : expression"
    p[0] = [p[1]]


def p_expression_binop(p):
    """expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression
                  | expression EQ expression
                  | expression NE expression
                  | expression LT expression
                  | expression LE expression
                  | expression GT expression
                  | expression GE expression
                  | expression AND expression
                  | expression OR expression"""
    p[0] = BinOp(p[1], p[2], p[3])


def p_expression_not(p):
    "expression : NOT expression"
    p[0] = UnaryOp(p[1], p[2])


def p_expression_uminus(p):
    "expression : MINUS expression %prec UMINUS"
    p[0] = UnaryOp(p[1], p[2])


def p_expression_group(p):
    "expression : LPAREN expression RPAREN"
    p[0] = p[2]


def p_expression_number(p):
    """expression : INTEGER_LITERAL
                  | REAL_LITERAL"""
    p[0] = Num(p[1])


def p_expression_string(p):
    "expression : STRING_LITERAL"
    p[0] = String(p[1])


def p_expression_logical(p):
    """expression : TRUE
                  | FALSE"""
    p[0] = LogicalConst(p.slice[1].type == "TRUE")


def p_expression_variable(p):
    "expression : variable_ref"
    p[0] = p[1]


def p_variable_ref_id(p):
    "variable_ref : ID"
    p[0] = Var(p[1])


def p_variable_ref_args(p):
    "variable_ref : ID LPAREN expression_list RPAREN"
    args = ", ".join(expr_to_text(arg) for arg in p[3])
    p[0] = Var(f"{p[1]}({args})")


def p_error(p):
    if p is None:
        raise SyntaxError("Syntax error at end of file")

    raise SyntaxError(
        f"Syntax error at line {p.lineno}: unexpected token {p.type} ({p.value!r})"
    )


parser = yacc.yacc(debug=False, write_tables=False)


def parse(source):
    lexer.lineno = 1
    return parser.parse(source, lexer=lexer)
