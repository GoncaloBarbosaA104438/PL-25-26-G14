"""Small command-line test runner for compiler stages."""

from argparse import ArgumentParser
from pathlib import Path

from src.lexer import lexer


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


def run_parser(_source: str) -> None:
    raise SystemExit("Parser mode is not available yet.")


def run_ast(_source: str) -> None:
    raise SystemExit("AST output mode is not available yet.")


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
