"""Small command-line test runner for compiler stages."""

from argparse import ArgumentParser
from pathlib import Path

import src.ast_nodes as ast_nodes
from src.lexer import lexer
from src.parser import parse


PROJECT_ROOT = Path(__file__).resolve().parent
TESTS_DIR = PROJECT_ROOT / "tests"


def resolve_source_path(filename: str) -> Path:
    path = Path(filename)
    if path.exists():
        return path

    test_path = TESTS_DIR / filename
    if test_path.exists():
        return test_path

    raise SystemExit(f"Input file not found: {filename}")


def read_source(filename: str) -> str:
    return resolve_source_path(filename).read_text(encoding="utf-8")


def run_lexer(source: str) -> None:
    lexer.lineno = 1
    lexer.input(source)

    for token in lexer:
        print(token)


def run_parser(source: str) -> None:
    parse(source)
    print("Syntax OK")


def format_ast(value, indent: int = 0) -> str:
    prefix = " " * indent

    if isinstance(value, list):
        if not value:
            return "[]"

        lines = ["["]
        for item in value:
            lines.append(f"{' ' * (indent + 2)}{format_ast(item, indent + 2)},")
        lines.append(f"{prefix}]")
        return "\n".join(lines)

    if value.__class__.__module__ == ast_nodes.__name__:
        attrs = vars(value)
        if not attrs:
            return f"{value.__class__.__name__}()"

        lines = [f"{value.__class__.__name__}("]
        for name, attr_value in attrs.items():
            rendered = format_ast(attr_value, indent + 2)
            lines.append(f"{' ' * (indent + 2)}{name}={rendered},")
        lines.append(f"{prefix})")
        return "\n".join(lines)

    return repr(value)


def run_ast(source: str) -> None:
    tree = parse(source)
    print(format_ast(tree))


def build_arg_parser() -> ArgumentParser:
    parser = ArgumentParser(description="Test compiler stages.")
    parser.add_argument("filename", help="Fortran source file to test.")

    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("-lexer", action="store_true", help="Print lexer tokens.")
    modes.add_argument("-parser", action="store_true", help="Run parser checks.")
    modes.add_argument("-ast", action="store_true", help="Print the generated AST.")

    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    source = read_source(args.filename)

    if args.lexer:
        run_lexer(source)
    elif args.parser:
        run_parser(source)
    elif args.ast:
        run_ast(source)


if __name__ == "__main__":
    main()
