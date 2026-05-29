import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lark
from src.parser import analizar_archivo, analizar_linea, obtener_parser
from src.ast_nodes import mostrar_ast

# Mapa de nombres de tokens de Lark a representacion legible
_TOKEN_LEGIBLE = {
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


def _token_a_legible(token: str) -> str:
    return _TOKEN_LEGIBLE.get(token, f"'{token.lower()}'")


def formatear_error(error: Exception) -> str:
    if isinstance(error, lark.UnexpectedCharacters):
        return (
            f"Error lexico [linea {error.line}, columna {error.column}]: "
            f"caracter inesperado '{error.char}'"
        )
    if isinstance(error, lark.UnexpectedToken):
        esperado = ", ".join(_token_a_legible(t) for t in error.expected)
        return (
            f"Error sintactico [linea {error.line}, columna {error.column}]: "
            f"se esperaba {esperado}, se encontro '{error.token.value}'"
        )
    if isinstance(error, lark.LarkError):
        return f"Error sintactico: {error}"
    return f"Error: {error}"


def ejecutar_archivo(ruta: str):
    try:
        programa = analizar_archivo(ruta)
        print("--- Analisis sintactico exitoso ---")
        print()
        print(mostrar_ast(programa))
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


def ejecutar_repl():
    print("=== TurnGame REPL ===")
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
    if len(sys.argv) > 1:
        ruta = sys.argv[1]
        ejecutar_archivo(ruta)
    else:
        ejecutar_repl()


if __name__ == "__main__":
    main()
