# pyright: ignore[reportShadowedImports]

"""AST node definitions for the Fortran 77 compiler."""

from dataclasses import dataclass
from typing import Any, Optional, Union


@dataclass
class Program:
    name: str
    declarations: list[Any]
    statements: list[Any]


@dataclass
class VarDecl:
    type: str
    variables: list[str]


@dataclass
class Assign:
    target: Any
    value: Any
    label_id: Optional[int] = None


@dataclass
class Print:
    values: list[Any]
    label_id: Optional[int] = None


@dataclass
class Read:
    targets: list[Any]
    label_id: Optional[int] = None


@dataclass
class IfThenElse:
    condition: Any
    if_block: list[Any]
    else_block: list[Any]
    label_id: Optional[int] = None


@dataclass
class DoHeader:
    label: int
    var: str
    start: Any
    end: Any
    label_id: Optional[int] = None


@dataclass
class Goto:
    target_label: int
    label_id: Optional[int] = None


@dataclass
class Continue:
    label_id: Optional[int] = None


@dataclass
class BinOp:
    left: Any
    op: str
    right: Any


@dataclass
class UnaryOp:
    op: str
    expr: Any


@dataclass
class Num:
    value: Union[int, float]


@dataclass
class Var:
    name: str


@dataclass
class String:
    value: str


@dataclass
class LogicalConst:
    value: bool

@dataclass
class ArrayDecl:
    def __init__(self, name, size):
        self.name = name
        self.size = size # Deve ser a expressão do tamanho, ex: Num(5)
    def __repr__(self):
        return f"ArrayDecl(name={self.name!r}, size={self.size!r})"

@dataclass
class ArrayRef:
    def __init__(self, name, args):
        self.name = name
        self.args = args # Lista de expressões (os índices)
    def __repr__(self):
        return f"ArrayRef(name={self.name!r}, args={self.args!r})"
