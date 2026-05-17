from typing import Any

from src.ast_nodes import (
    ArrayDecl,
    ArrayRef,
    Assign,
    BinOp,
    Continue,
    DoHeader,
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


class AstOptimizer:
    arithmetic_ops = {"+", "-", "*", "/"}

    def optimize(self, ast: Program) -> Program:
        self.fold_constants_program(ast)
        used_variables = self.collect_used_variables(ast.statements)
        self.remove_unused_declarations(ast, used_variables)
        return ast

    def fold_constants_program(self, program: Program) -> None:
        for declaration in program.declarations:
            self.fold_constants_declaration(declaration)

        program.statements = self.fold_constants_statements(program.statements)

    def fold_constants_declaration(self, declaration: VarDecl) -> None:
        for variable in declaration.variables:
            if isinstance(variable, ArrayDecl):
                variable.size = self.fold_expr(variable.size)

    def fold_constants_statements(self, statements: list[Any]) -> list[Any]:
        return [self.fold_statement(statement) for statement in statements]

    def fold_statement(self, statement):
        if isinstance(statement, Assign):
            statement.target = self.fold_target(statement.target)
            statement.value = self.fold_expr(statement.value)
            return statement

        if isinstance(statement, Print):
            statement.values = [self.fold_expr(value) for value in statement.values]
            return statement

        if isinstance(statement, Read):
            statement.targets = [
                self.fold_target(target) for target in statement.targets
            ]
            return statement

        if isinstance(statement, IfThenElse):
            statement.condition = self.fold_expr(statement.condition)
            statement.if_block = self.fold_constants_statements(statement.if_block)
            statement.else_block = self.fold_constants_statements(statement.else_block)
            return statement

        if isinstance(statement, DoHeader):
            statement.start = self.fold_expr(statement.start)
            statement.end = self.fold_expr(statement.end)
            return statement

        return statement

    def fold_target(self, target):
        if isinstance(target, ArrayRef):
            target.args = [self.fold_expr(arg) for arg in target.args]
        return target

    def fold_expr(self, expr):
        if isinstance(expr, UnaryOp):
            expr.expr = self.fold_expr(expr.expr)
            if expr.op == "-" and isinstance(expr.expr, Num):
                return Num(-expr.expr.value)
            return expr

        if isinstance(expr, BinOp):
            expr.left = self.fold_expr(expr.left)
            expr.right = self.fold_expr(expr.right)
            if self.can_fold_binop(expr):
                return Num(self.evaluate_binop(expr))
            return expr

        if isinstance(expr, ArrayRef):
            expr.args = [self.fold_expr(arg) for arg in expr.args]
            return expr

        return expr

    def can_fold_binop(self, expr: BinOp) -> bool:
        if not (
            expr.op in self.arithmetic_ops
            and isinstance(expr.left, Num)
            and isinstance(expr.right, Num)
        ):
            return False
            
        #divisão por zero
        if expr.op == "/" and expr.right.value == 0:
            return False
            
        return True

    def evaluate_binop(self, expr: BinOp):
        left = expr.left.value
        right = expr.right.value

        if expr.op == "+":
            result = left + right
        elif expr.op == "-":
            result = left - right
        elif expr.op == "*":
            result = left * right
        else:
            result = self.divide_constants(left, right)

        if isinstance(left, float) or isinstance(right, float):
            return float(result)
        return result

    def divide_constants(self, left, right):
        if isinstance(left, float) or isinstance(right, float):
            return left / right
        return left // right

    def collect_used_variables(self, statements: list[Any]) -> set[str]:
        used: set[str] = set()
        for statement in statements:
            self.collect_statement_variables(statement, used)
        return used

    def collect_statement_variables(self, statement, used: set[str]) -> None:
        if isinstance(statement, Assign):
            self.collect_target_variables(statement.target, used)
            self.collect_expr_variables(statement.value, used)
            return

        if isinstance(statement, Print):
            for value in statement.values:
                self.collect_expr_variables(value, used)
            return

        if isinstance(statement, Read):
            for target in statement.targets:
                self.collect_target_variables(target, used)
            return

        if isinstance(statement, IfThenElse):
            self.collect_expr_variables(statement.condition, used)
            for child in statement.if_block:
                self.collect_statement_variables(child, used)
            for child in statement.else_block:
                self.collect_statement_variables(child, used)
            return

        if isinstance(statement, DoHeader):
            used.add(statement.var)
            self.collect_expr_variables(statement.start, used)
            self.collect_expr_variables(statement.end, used)

    def collect_target_variables(self, target, used: set[str]) -> None:
        if isinstance(target, Var):
            used.add(target.name)
            return

        if isinstance(target, ArrayRef):
            used.add(target.name)
            for arg in target.args:
                self.collect_expr_variables(arg, used)

    def collect_expr_variables(self, expr, used: set[str]) -> None:
        if isinstance(expr, Var):
            used.add(expr.name)
            return

        if isinstance(expr, ArrayRef):
            used.add(expr.name)
            for arg in expr.args:
                self.collect_expr_variables(arg, used)
            return

        if isinstance(expr, UnaryOp):
            self.collect_expr_variables(expr.expr, used)
            return

        if isinstance(expr, BinOp):
            self.collect_expr_variables(expr.left, used)
            self.collect_expr_variables(expr.right, used)

    def remove_unused_declarations(self, program: Program, used_variables: set[str]) -> None:
        kept_declarations: list[VarDecl] = []

        for declaration in program.declarations:
            declaration.variables = [
                variable
                for variable in declaration.variables
                if self.declared_name(variable) in used_variables
            ]
            if declaration.variables:
                kept_declarations.append(declaration)

        program.declarations = kept_declarations

    def declared_name(self, variable) -> str:
        if isinstance(variable, ArrayDecl):
            return variable.name
        return variable
