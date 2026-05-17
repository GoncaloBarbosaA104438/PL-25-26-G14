from dataclasses import dataclass
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


class SemanticError(Exception):
    """Raised when semantic validation fails."""


@dataclass
class Symbol:
    type: str
    is_array: bool = False
    size: Any = None


class SemanticAnalyzer:
    numeric_types = {"INTEGER", "REAL"}
    relational_ops = {".EQ.", ".NE.", ".LT.", ".LE.", ".GT.", ".GE."}
    arithmetic_ops = {"+", "-", "*", "/"}
    logical_ops = {".AND.", ".OR."}
    intrinsic_functions = {"MOD", "SIN", "COS", "INT", "REAL"}

    def __init__(self, ast: Program):
        self.ast = ast
        self.symbols: dict[str, Symbol] = {}
        self.defined_labels: set[int] = set()

    def analyze(self) -> None:
        self.collect_labels(self.ast.statements)
        self.visit(self.ast)
        
    def collect_labels(self, statements: list[Any]) -> None:
        for stmt in statements:
            if getattr(stmt, 'label_id', None) is not None:
                if stmt.label_id in self.defined_labels:
                    raise SemanticError(f"Duplicate label {stmt.label_id} detected")
                self.defined_labels.add(stmt.label_id)
            
            # dentro dos ifs
            if isinstance(stmt, IfThenElse):
                self.collect_labels(stmt.if_block)
                self.collect_labels(stmt.else_block)

    def visit(self, node):
        method_name = f"visit_{node.__class__.__name__}"
        method = getattr(self, method_name, None)
        if method is None:
            raise SemanticError(f"No semantic visitor for {node.__class__.__name__}")
        return method(node)

    def visit_Program(self, node: Program) -> None:
        for declaration in node.declarations:
            self.visit(declaration)

        self.validate_do_labels(node.statements)

        for statement in node.statements:
            self.visit(statement)

    def visit_VarDecl(self, node: VarDecl) -> None:
        for variable in node.variables:
            if isinstance(variable, ArrayDecl):
                self.declare_array(node.type, variable)
            else:
                self.declare_scalar(node.type, variable)

    def declare_scalar(self, var_type: str, name: str) -> None:
        if name in self.symbols:
            raise SemanticError(f"Variable {name} declared more than once")
        self.symbols[name] = Symbol(var_type)

    def declare_array(self, var_type: str, node: ArrayDecl) -> None:
        if node.name in self.symbols:
            raise SemanticError(f"Variable {node.name} declared more than once")

        size_type = self.visit(node.size)
        if size_type != "INTEGER":
            raise SemanticError(f"Array {node.name} size must be INTEGER")

        self.symbols[node.name] = Symbol(var_type, is_array=True, size=node.size)

    def visit_Assign(self, node: Assign) -> None:
        target_type = self.visit_assignment_target(node.target)
        value_type = self.visit(node.value)

        if not self.types_compatible(target_type, value_type):
            raise SemanticError(
                f"Cannot assign {value_type} expression to {target_type} target"
            )

    def visit_Print(self, node: Print) -> None:
        for value in node.values:
            self.visit(value)

    def visit_Read(self, node: Read) -> None:
        for target in node.targets:
            self.visit_assignment_target(target)

    def visit_IfThenElse(self, node: IfThenElse) -> None:
        condition_type = self.visit(node.condition)
        if condition_type != "LOGICAL":
            raise SemanticError("IF condition must be LOGICAL")

        for statement in node.if_block:
            self.visit(statement)

        for statement in node.else_block:
            self.visit(statement)

    def visit_DoHeader(self, node: DoHeader) -> None:
        self.require_declared_scalar(node.var)
        var_type = self.symbols[node.var].type
        if var_type != "INTEGER":
            raise SemanticError(f"DO variable {node.var} must be INTEGER")

        start_type = self.visit(node.start)
        end_type = self.visit(node.end)
        if start_type != "INTEGER" or end_type != "INTEGER":
            raise SemanticError(f"DO loop with label {node.label} requires INTEGER bounds")

    def visit_Goto(self, node: Goto) -> None:
        if node.target_label not in self.defined_labels:
            raise SemanticError(f"GOTO target label {node.target_label} does not exist")

    def visit_Continue(self, node: Continue) -> None:
        return None

    def visit_BinOp(self, node: BinOp) -> str:
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)

        if node.op in self.arithmetic_ops:
            self.require_numeric(left_type, node.op)
            self.require_numeric(right_type, node.op)
            return "REAL" if "REAL" in {left_type, right_type} else "INTEGER"

        if node.op in self.relational_ops:
            self.require_numeric(left_type, node.op)
            self.require_numeric(right_type, node.op)
            return "LOGICAL"

        if node.op in self.logical_ops:
            if left_type != "LOGICAL" or right_type != "LOGICAL":
                raise SemanticError(f"Operator {node.op} requires LOGICAL operands")
            return "LOGICAL"

        raise SemanticError(f"Unsupported binary operator {node.op}")

    def visit_UnaryOp(self, node: UnaryOp) -> str:
        expr_type = self.visit(node.expr)

        if node.op == "-":
            self.require_numeric(expr_type, node.op)
            return expr_type

        if node.op == ".NOT.":
            if expr_type != "LOGICAL":
                raise SemanticError("Operator .NOT. requires a LOGICAL operand")
            return "LOGICAL"

        raise SemanticError(f"Unsupported unary operator {node.op}")

    def visit_Num(self, node: Num) -> str:
        if isinstance(node.value, float):
            return "REAL"
        return "INTEGER"

    def visit_Var(self, node: Var) -> str:
        symbol = self.require_declared(node.name)
        if symbol.is_array:
            raise SemanticError(f"Array {node.name} used without index")
        return symbol.type

    def visit_ArrayRef(self, node: ArrayRef) -> str:
        if node.name in self.intrinsic_functions:
            return self.visit_intrinsic_function(node)

        symbol = self.require_declared(node.name)
        if not symbol.is_array:
            raise SemanticError(f"Variable {node.name} used as an array")

        for arg in node.args:
            arg_type = self.visit(arg)
            if arg_type != "INTEGER":
                raise SemanticError(f"Array {node.name} index must be INTEGER")

        return symbol.type

    def visit_intrinsic_function(self, node: ArrayRef) -> str:
        if node.name == "MOD":
            if len(node.args) != 2:
                raise SemanticError("MOD expects exactly two arguments")

            left_type = self.visit(node.args[0])
            right_type = self.visit(node.args[1])
            self.require_numeric(left_type, "MOD")
            self.require_numeric(right_type, "MOD")
            return "REAL" if "REAL" in {left_type, right_type} else "INTEGER"

        if node.name in {"SIN", "COS"}:
            if len(node.args) != 1:
                raise SemanticError(f"{node.name} expects exactly one argument")

            arg_type = self.visit(node.args[0])
            self.require_numeric(arg_type, node.name)
            if arg_type != "REAL":
                raise SemanticError(f"{node.name} expects a REAL argument")
            return "REAL"

        if node.name == "INT":
            if len(node.args) != 1:
                raise SemanticError("INT expects exactly one argument")

            arg_type = self.visit(node.args[0])
            if arg_type != "REAL":
                raise SemanticError("INT expects a REAL argument")
            return "INTEGER"

        if node.name == "REAL":
            if len(node.args) != 1:
                raise SemanticError("REAL expects exactly one argument")

            arg_type = self.visit(node.args[0])
            if arg_type != "INTEGER":
                raise SemanticError("REAL expects an INTEGER argument")
            return "REAL"

        raise SemanticError(f"Unsupported intrinsic function {node.name}")

    def visit_String(self, node: String) -> str:
        return "STRING"

    def visit_LogicalConst(self, node: LogicalConst) -> str:
        return "LOGICAL"

    def visit_assignment_target(self, node) -> str:
        if isinstance(node, Var):
            symbol = self.require_declared(node.name)
            if symbol.is_array:
                raise SemanticError(f"Array {node.name} assignment requires an index")
            return symbol.type

        if isinstance(node, ArrayRef):
            if node.name in self.intrinsic_functions:
                raise SemanticError(
                    f"Intrinsic function {node.name} cannot be an assignment target"
                )
            return self.visit_ArrayRef(node)

        raise SemanticError(f"Invalid assignment target {node!r}")

    def require_declared(self, name: str) -> Symbol:
        symbol = self.symbols.get(name)
        if symbol is None:
            raise SemanticError(f"Variable {name} used before declaration")
        return symbol

    def require_declared_scalar(self, name: str) -> None:
        symbol = self.require_declared(name)
        if symbol.is_array:
            raise SemanticError(f"Array {name} cannot be used as a scalar variable")

    def require_numeric(self, value_type: str, op: str) -> None:
        if value_type not in self.numeric_types:
            raise SemanticError(f"Operator {op} requires numeric operands")

    def types_compatible(self, target_type: str, value_type: str) -> bool:
        if target_type == value_type:
            return True
        return target_type == "REAL" and value_type == "INTEGER"

    def validate_do_labels(self, statements: list[Any]) -> None:
        for index, statement in enumerate(statements):
            if isinstance(statement, DoHeader):
                if not self.has_later_continue(statements, index + 1, statement.label):
                    raise SemanticError(
                        f"Missing CONTINUE for DO loop with label {statement.label}"
                    )

            if isinstance(statement, IfThenElse):
                self.validate_do_labels(statement.if_block)
                self.validate_do_labels(statement.else_block)

    def has_later_continue(
        self, statements: list[Any], start_index: int, label: int
    ) -> bool:
        for statement in statements[start_index:]:
            if isinstance(statement, Continue) and statement.label_id == label:
                return True
        return False
