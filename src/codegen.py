"""EWVM code generation for the Fortran 77 compiler MVP."""

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


class CodeGenerator:
    def __init__(self):
        self.address_map: dict[str, int] = {}
        self.type_map: dict[str, str] = {}
        self.array_names: set[str] = set()
        self.loop_contexts: dict[int, dict[str, Any]] = {}
        self.var_declarations: list[str] = []
        self.main_code: list[str] = []
        self.next_address = 0
        self.label_counter = 0

    def generate(self, ast: Program) -> list[str]:
        self.reset()
        self.visit(ast)
        return [*self.var_declarations, "start", *self.main_code, "stop"]

    def reset(self) -> None:
        self.address_map = {}
        self.type_map = {}
        self.array_names = set()
        self.loop_contexts = {}
        self.var_declarations = []
        self.main_code = []
        self.next_address = 0
        self.label_counter = 0

    def emit(self, instruction: str) -> None:
        self.main_code.append(instruction)

    def emit_decl(self, instruction: str) -> None:
        self.var_declarations.append(instruction)

    def visit(self, node):
        method_name = f"visit_{node.__class__.__name__}"
        method = getattr(self, method_name)
        return method(node)

    def visit_Program(self, node: Program) -> None:
        self.allocate_declarations(node.declarations)
        self.visit_statements(node.statements)

    def allocate_declarations(self, declarations: list[VarDecl]) -> None:
        for declaration in declarations:
            for variable in declaration.variables:
                if isinstance(variable, ArrayDecl):
                    self.allocate_array(declaration.type, variable)
                else:
                    self.allocate_scalar(declaration.type, variable)

    def allocate_scalar(self, var_type: str, name: str) -> None:
        self.address_map[name] = self.next_address
        self.type_map[name] = var_type
        self.next_address += 1

        self.emit_decl("pushi 0")
        self.emit_decl(f"storeg {self.address_map[name]}")

    def allocate_array(self, var_type: str, node: ArrayDecl) -> None:
        self.address_map[node.name] = self.next_address
        self.type_map[node.name] = var_type
        self.array_names.add(node.name)
        self.next_address += 1

        self.emit_expr_to(node.size, self.var_declarations)
        self.emit_decl("allocn")
        self.emit_decl(f"storeg {self.address_map[node.name]}")

    def visit_statements(self, statements: list[Any]) -> None:
        for statement in statements:
            self.emit_source_label(statement)
            self.visit(statement)

    def emit_source_label(self, node) -> None:
        label_id = getattr(node, "label_id", None)
        if label_id is not None:
            self.emit(f"L{label_id}:")

    def visit_Assign(self, node: Assign) -> None:
        if isinstance(node.target, ArrayRef):
            self.emit_array_location(node.target)
            self.visit(node.value)
            self.emit("storen")
            return

        self.visit(node.value)
        self.emit(f"storeg {self.address_map[node.target.name]}")

    def visit_Print(self, node: Print) -> None:
        for value in node.values:
            self.visit(value)
            value_type = self.expr_type(value)
            if value_type == "STRING":
                self.emit("writes")
            elif value_type == "REAL":
                self.emit("writef")
            else:
                self.emit("writei")
        self.emit("writeln")

    def visit_Read(self, node: Read) -> None:
        for target in node.targets:
            if isinstance(target, ArrayRef):
                self.emit_array_location(target)
                self.emit("read")
                self.emit("atof" if self.target_type(target) == "REAL" else "atoi")
                self.emit("storen")
                continue

            self.emit("read")
            if self.target_type(target) == "REAL":
                self.emit("atof")
            else:
                self.emit("atoi")
            self.emit(f"storeg {self.address_map[target.name]}")

    def visit_IfThenElse(self, node: IfThenElse) -> None:
        else_label = self.new_label("ELSE")
        end_label = self.new_label("ENDIF")

        self.visit(node.condition)
        self.emit(f"jz {else_label}")
        self.visit_statements(node.if_block)
        self.emit(f"jump {end_label}")
        self.emit(f"{else_label}:")
        self.visit_statements(node.else_block)
        self.emit(f"{end_label}:")

    def visit_DoHeader(self, node: DoHeader) -> None:
        var_address = self.address_map[node.var]
        start_label = f"DOSTART{node.label}"
        end_label = f"DOEND{node.label}"

        self.visit(node.start)
        self.emit(f"storeg {var_address}")
        self.loop_contexts[node.label] = {
            "var": node.var,
            "start_label": start_label,
            "end_label": end_label,
        }

        self.emit(f"{start_label}:")
        self.emit(f"pushg {var_address}")
        self.visit(node.end)
        self.emit("sup")
        self.emit("not")
        self.emit(f"jz {end_label}")

    def visit_Goto(self, node: Goto) -> None:
        self.emit(f"jump L{node.target_label}")

    def visit_Continue(self, node: Continue) -> None:
        context = self.loop_contexts.get(node.label_id)
        if context is None:
            return

        var_address = self.address_map[context["var"]]
        self.emit(f"pushg {var_address}")
        self.emit("pushi 1")
        self.emit("add")
        self.emit(f"storeg {var_address}")
        self.emit(f"jump {context['start_label']}")
        self.emit(f"{context['end_label']}:")

    def visit_BinOp(self, node: BinOp) -> None:
        self.visit(node.left)
        self.visit(node.right)
        self.emit(self.binary_instruction(node))

        if node.op == ".NE.":
            self.emit("not")

    def visit_UnaryOp(self, node: UnaryOp) -> None:
        self.visit(node.expr)
        if node.op == ".NOT.":
            self.emit("not")
        elif node.op == "-":
            self.emit("pushi -1")
            self.emit("mul")

    def visit_Num(self, node: Num) -> None:
        if isinstance(node.value, float):
            self.emit(f"pushf {node.value}")
        else:
            self.emit(f"pushi {node.value}")

    def visit_Var(self, node: Var) -> None:
        self.emit(f"pushg {self.address_map[node.name]}")

    def visit_ArrayRef(self, node: ArrayRef) -> None:
        if node.name == "MOD":
            self.visit(node.args[0])
            self.visit(node.args[1])
            self.emit("mod")
            return

        self.emit_array_location(node)
        self.emit("loadn")

    def visit_String(self, node: String) -> None:
        escaped = node.value.replace("\\", "\\\\").replace('"', '\\"')
        self.emit(f'pushs "{escaped}"')

    def visit_LogicalConst(self, node: LogicalConst) -> None:
        self.emit(f"pushi {1 if node.value else 0}")

    def emit_array_location(self, node: ArrayRef) -> None:
        self.emit(f"pushg {self.address_map[node.name]}")
        self.visit(node.args[0])
        self.emit("pushi 1")
        self.emit("sub")

    def emit_expr_to(self, node, output: list[str]) -> None:
        original = self.main_code
        self.main_code = output
        self.visit(node)
        self.main_code = original

    def binary_instruction(self, node: BinOp) -> str:
        if node.op == "+":
            return "add"
        if node.op == "-":
            return "sub"
        if node.op == "*":
            return "mul"
        if node.op == "/":
            return "fdiv" if self.expr_type(node) == "REAL" else "div"
        if node.op == ".EQ.":
            return "equal"
        if node.op == ".NE.":
            return "equal"
        if node.op == ".LT.":
            return "inf"
        if node.op == ".LE.":
            return "infeq"
        if node.op == ".GT.":
            return "sup"
        if node.op == ".GE.":
            return "supeq"
        if node.op == ".AND.":
            return "and"
        if node.op == ".OR.":
            return "or"
        raise ValueError(f"Unsupported operator {node.op}")

    def target_type(self, target) -> str:
        if isinstance(target, Var):
            return self.type_map[target.name]
        if isinstance(target, ArrayRef):
            return self.type_map[target.name]
        return "INTEGER"

    def expr_type(self, node) -> str:
        if isinstance(node, Num):
            return "REAL" if isinstance(node.value, float) else "INTEGER"
        if isinstance(node, String):
            return "STRING"
        if isinstance(node, LogicalConst):
            return "LOGICAL"
        if isinstance(node, Var):
            return self.type_map[node.name]
        if isinstance(node, ArrayRef):
            if node.name == "MOD":
                has_real_arg = any(self.expr_type(arg) == "REAL" for arg in node.args)
                return "REAL" if has_real_arg else "INTEGER"
            return self.type_map[node.name]
        if isinstance(node, UnaryOp):
            return "LOGICAL" if node.op == ".NOT." else self.expr_type(node.expr)
        if isinstance(node, BinOp):
            logical_result_ops = {
                ".EQ.",
                ".NE.",
                ".LT.",
                ".LE.",
                ".GT.",
                ".GE.",
                ".AND.",
                ".OR.",
            }
            if node.op in logical_result_ops:
                return "LOGICAL"
            has_real_operand = (
                self.expr_type(node.left) == "REAL"
                or self.expr_type(node.right) == "REAL"
            )
            return (
                "REAL"
                if has_real_operand
                else "INTEGER"
            )
        return "INTEGER"

    def new_label(self, prefix: str) -> str:
        label = f"{prefix}{self.label_counter}"
        self.label_counter += 1
        return label
