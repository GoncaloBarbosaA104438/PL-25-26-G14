import argparse
import sys
from pathlib import Path

from src.codegen import CodeGenerator
from src.optimizer import AstOptimizer
from src.parser import parse
from src.semantic import SemanticAnalyzer, SemanticError


def compile_source(source: str, optimize: bool = False) -> list[str]:
    ast = parse(source)
    SemanticAnalyzer(ast).analyze()
    if optimize:
        ast = AstOptimizer().optimize(ast)
    return CodeGenerator().generate(ast)


def default_output_path(input_path: Path) -> Path:
    return input_path.with_suffix(".vm")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compile Fortran 77 to EWVM.")
    parser.add_argument("source", help="Path to the Fortran source file.")
    parser.add_argument(
        "-o",
        "--output",
        help="Path to the generated EWVM assembly file.",
    )
    parser.add_argument(
        "-O",
        "--optimize",
        action="store_true",
        help="Run AST optimization before code generation.",
    )
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    input_path = Path(args.source)
    output_path = Path(args.output) if args.output else default_output_path(input_path)

    try:
        source = input_path.read_text(encoding="utf-8")
        instructions = compile_source(source, args.optimize)
        output_path.write_text("\n".join(instructions) + "\n", encoding="utf-8")
    except (SyntaxError, SemanticError) as error:
        print(f"ERRO: {error}", file=sys.stderr)
        sys.exit(1)
    except OSError as error:
        print(f"ERRO: {error}", file=sys.stderr)
        sys.exit(1)

    print(f"Compilação concluída: código gerado em {output_path}")


if __name__ == "__main__":
    main()
