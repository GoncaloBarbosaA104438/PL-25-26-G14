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
class DoLoop:
    label: int
    var: str
    start: Any
    end: Any
    block: list[Any]
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
