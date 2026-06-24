import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lark
from src.parser import analyze_file, analyze_line, get_parser
from src.ast_nodes import show_ast
from src.semantic_analyzer import analyze_semantics

# Mapa de nombres de tokens de Lark a representacion legible
_READABLE_TOKENS = {
    "SEMICOLON": "';'",
    "PLUS": "'+'",
    "MINUS": "'-'",
    "TIMES": "'*'",
    "DIVIDE": "'/'",
    "ASSIGN": "'='",
    "EQ": "'=='",
    "NEQ": "'!='",
    "LT": "'<'",
    "GT": "'>'",
    "LTE": "'<='",
    "GTE": "'>='",
    "DOT": "'.'",
    "LPAREN": "'('",
    "RPAREN": "')'",
    "LBRACE": "'{'",
    "RBRACE": "'}'",
    "CHARACTER": "'character'",
    "HP": "'hp'",
    "MP": "'mp'",
    "MP_REGEN": "'mp_regen'",
    "ATK": "'atk'",
    "DEF": "'def'",
    "TURN": "'turn'",
    "USE": "'use'",
    "ON": "'on'",
    "REPEAT": "'repeat'",
    "TIMES_KW": "'times'",
    "IF": "'if'",
    "THEN": "'then'",
    "ELSE": "'else'",
    "END": "'end'",
    "WHILE": "'while'",
    "DO": "'do'",
    "NUMBER_TYPE": "'number'",
    "PRINT": "'print'",
    "NUMBER": "numero",
    "STRING": "cadena",
    "IDENTIFIER": "identificador",
}


def _translate_token(token: str) -> str:
    return _READABLE_TOKENS.get(token, f"'{token.lower()}'")


def format_error(error: Exception) -> str:
    if isinstance(error, lark.UnexpectedCharacters):
        return (
            f"Error léxico [línea {error.line}, columna {error.column}]: "
            f"carácter inesperado '{error.char}'"
        )
    if isinstance(error, lark.UnexpectedToken):
        expected = ", ".join(_translate_token(t) for t in error.expected)
        found = "<fin de archivo>" if error.token.type == "$END" else error.token.value
        return (
            f"Error sintáctico [línea {error.line}, columna {error.column}]: "
            f"se esperaba {expected}, se encontró '{found}'"
        )
    if isinstance(error, lark.LarkError):
        return f"Error sintáctico: {error}"
    return f"Error: {error}"


def execute_file(path: str, show_tree: bool = True):
    syntax_errors: list[str] = []

    SYNC_TOKENS = {"SEMICOLON", "RBRACE", "END", "ELSE"}

    def recovery_handler(error):
        syntax_errors.append(format_error(error))
        ip = error.interactive_parser
        gen = ip.lexer_state.lex(ip.parser_state)
        while True:
            try:
                token = next(gen)
            except StopIteration:
                break
            except lark.UnexpectedToken:
                gen = ip.lexer_state.lex(ip.parser_state)
                continue
            try:
                ip.parser_state.feed_token(token)
            except lark.UnexpectedToken:
                continue
            if token.type in SYNC_TOKENS:
                break
        return True

    try:
        program = analyze_file(path, on_error=recovery_handler)
    except lark.LarkError as e:
        if not syntax_errors:
            syntax_errors.append(format_error(e))
    except FileNotFoundError:
        print(f"Error: archivo '{path}' no encontrado")
        sys.exit(1)
    except Exception as e:
        print(f"Error inesperado: {e}")
        traceback.print_exc()
        sys.exit(1)

    if syntax_errors:
        print(f"Se encontraron {len(syntax_errors)} error(es) sintactico(s):")
        print()
        for e in syntax_errors:
            print(f"  {e}")
        sys.exit(1)

    # Analisis semantico
    errors = analyze_semantics(program)
    if errors:
        print(f"Se encontraron {len(errors)} error(es) semantico(s):")
        print()
        for e in errors:
            print(f"  {e}")
        sys.exit(1)

    print("--- Analisis completado: programa valido ---")
    if show_tree:
        print()
        print(show_ast(program))


def run_repl():
    print("=== TurnGame REPL ===")
    print("Solo analisis sintactico (sin validacion semantica)")
    print("Escribe 'salir' para terminar")
    print()
    while True:
        try:
            line = input(">> ")
            text = line.strip()
            if text.lower() == "salir":
                break
            if not text:
                continue
            try:
                node = analyze_line(text)
                print(show_ast(node))
                print()
            except lark.LarkError as e:
                print(format_error(e))
                print()
        except EOFError:
            break
        except KeyboardInterrupt:
            print()
            break


def main():
    show_tree = True
    args = [a for a in sys.argv[1:] if a]

    if "--no-ast" in args:
        show_tree = False
        args.remove("--no-ast")

    if args:
        path = args[0]
        execute_file(path, show_tree=show_tree)
    else:
        run_repl()


if __name__ == "__main__":
    main()
