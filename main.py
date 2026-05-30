import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lark
from src.parser import analizar_archivo, analizar_linea, obtener_parser
from src.ast_nodes import mostrar_ast
from src.semantic_analyzer import analizar_semantica

# Mapa de nombres de tokens de Lark a representacion legible
_TOKENS_LEGIBLES = {
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
    "PERSONAJE": "'personaje'",
    "HP": "'hp'",
    "ATK": "'atk'",
    "DEF": "'def'",
    "TURNO": "'turno'",
    "USAR": "'usar'",
    "ATAQUE": "'ataque'",
    "EN": "'en'",
    "REPEAT": "'repeat'",
    "VECES": "'veces'",
    "SI": "'si'",
    "ENTONCES": "'entonces'",
    "SINO": "'sino'",
    "FIN": "'fin'",
    "MIENTRAS": "'mientras'",
    "HACER": "'hacer'",
    "NUMERO": "'numero'",
    "IMPRIMIR": "'imprimir'",
    "NUMBER": "numero",
    "STRING": "cadena",
    "IDENTIFIER": "identificador",
}


def _traducir_token(token: str) -> str:
    return _TOKENS_LEGIBLES.get(token, f"'{token.lower()}'")


def formatear_error(error: Exception) -> str:
    if isinstance(error, lark.UnexpectedCharacters):
        return (
            f"Error lexico [linea {error.line}, columna {error.column}]: "
            f"caracter inesperado '{error.char}'"
        )
    if isinstance(error, lark.UnexpectedToken):
        esperado = ", ".join(_traducir_token(t) for t in error.expected)
        return (
            f"Error sintactico [linea {error.line}, columna {error.column}]: "
            f"se esperaba {esperado}, se encontro '{error.token.value}'"
        )
    if isinstance(error, lark.LarkError):
        return f"Error sintactico: {error}"
    return f"Error: {error}"


def ejecutar_archivo(ruta: str, mostrar_arbol: bool = True):
    try:
        programa = analizar_archivo(ruta)
    except lark.LarkError as e:
        print(formatear_error(e))
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: archivo '{ruta}' no encontrado")
        sys.exit(1)
    except Exception as e:
        print(f"Error inesperado: {e}")
        traceback.print_exc()
        sys.exit(1)

    # Analisis semantico
    errores = analizar_semantica(programa)
    if errores:
        print(f"Se encontraron {len(errores)} error(es) semantico(s):")
        print()
        for e in errores:
            print(f"  {e}")
        sys.exit(1)

    print("--- Analisis completado: programa valido ---")
    if mostrar_arbol:
        print()
        print(mostrar_ast(programa))


def ejecutar_repl():
    print("=== TurnGame REPL ===")
    print("Solo analisis sintactico (sin validacion semantica)")
    print("Escribe 'salir' para terminar")
    print()
    while True:
        try:
            linea = input(">> ")
            texto = linea.strip()
            if texto.lower() == "salir":
                break
            if not texto:
                continue
            try:
                nodo = analizar_linea(texto)
                print(mostrar_ast(nodo))
                print()
            except lark.LarkError as e:
                print(formatear_error(e))
                print()
        except EOFError:
            break
        except KeyboardInterrupt:
            print()
            break


def main():
    mostrar_arbol = True
    args = [a for a in sys.argv[1:] if a]

    if "--no-ast" in args:
        mostrar_arbol = False
        args.remove("--no-ast")

    if args:
        ruta = args[0]
        ejecutar_archivo(ruta, mostrar_arbol=mostrar_arbol)
    else:
        ejecutar_repl()


if __name__ == "__main__":
    main()
