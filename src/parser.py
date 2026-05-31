from pathlib import Path
from typing import Any

import lark
from lark import Token, v_args

from .ast_nodes import (
    NodoAST,
    Programa,
    DeclPersonaje,
    Turno,
    Repeat,
    Si,
    Mientras,
    DeclVar,
    Asignacion,
    Imprimir,
    OpBinaria,
    OpUnaria,
    Literal,
    Identificador,
    AccesoAtributo,
    mostrar_ast,
)

RUTA_GRAMATICA = Path(__file__).resolve().parent.parent / "grammar.lark"


# ---------------------------------------------------------------------------
# Transformador: convierte el arbol de Lark (lark.Tree) en AST propio
# ---------------------------------------------------------------------------

class TransformadorAST(lark.Transformer):
    """Convierte cada regla de la gramatica en su nodo AST correspondiente."""

    # -- Programa -----------------------------------------------------------

    def program(self, hijos):
        return Programa(hijos)

    # -- Sentencias ---------------------------------------------------------

    def statement(self, hijos):
        return hijos[0]

    # -- Declaracion de personaje -------------------------------------------
    # stat_val: MINUS? NUMBER
    # personaje_decl: PERSONAJE IDENTIFIER HP ASSIGN stat_val ATK ASSIGN stat_val DEF ASSIGN stat_val SEMICOLON

    def stat_val(self, hijos):
        try:
            if len(hijos) == 1:
                return int(hijos[0])
            return -int(hijos[1])
        except ValueError:
            raise lark.GrammarError(
                f"El valor '{hijos[-1]}' debe ser un número entero, no decimal."
            )

    @v_args(meta=True)
    def personaje_decl(self, hijos, meta):
        nombre = str(hijos[1])
        hp = int(hijos[4])
        atk = int(hijos[7])
        defensa = int(hijos[10])
        return DeclPersonaje(nombre, hp, atk, defensa, meta.line, meta.column)

    # -- Turno de combate ---------------------------------------------------
    # turno_stmt: TURNO IDENTIFIER USAR ATAQUE EN IDENTIFIER SEMICOLON

    @v_args(meta=True)
    def turno_stmt(self, hijos, meta):
        atacante = str(hijos[1])
        victima = str(hijos[5])
        return Turno(atacante, victima, meta.line, meta.column)

    # -- Repeticion fija ----------------------------------------------------
    # repeat_stmt: REPEAT NUMBER VECES LBRACE statement* RBRACE

    @v_args(meta=True)
    def repeat_stmt(self, hijos, meta):
        veces = int(hijos[1])
        cuerpo = list(hijos[4:-1])
        return Repeat(veces, cuerpo, meta.line, meta.column)

    # -- Condicional si/sino/fin --------------------------------------------
    # si_stmt: SI condition ENTONCES LBRACE statement* RBRACE
    #          (SINO LBRACE statement* RBRACE)? FIN

    @v_args(meta=True)
    def si_stmt(self, hijos, meta):
        condicion = hijos[1]

        # Ubicar llaves de apertura/cierre
        indices_llave_abre = [
            i for i, c in enumerate(hijos)
            if isinstance(c, Token) and c.type == "LBRACE"
        ]
        indices_llave_cierra = [
            i for i, c in enumerate(hijos)
            if isinstance(c, Token) and c.type == "RBRACE"
        ]

        # Bloque "entonces": entre la primera LBRACE y la primera RBRACE
        entonces = list(hijos[indices_llave_abre[0] + 1:indices_llave_cierra[0]])

        # Bloque "sino" (opcional)
        if len(indices_llave_cierra) > 1:
            sino = list(hijos[indices_llave_abre[1] + 1:indices_llave_cierra[1]])
        else:
            sino = None

        return Si(condicion, entonces, sino, meta.line, meta.column)

    # -- Bucle mientras -----------------------------------------------------
    # mientras_stmt: MIENTRAS condition HACER LBRACE statement* RBRACE FIN

    @v_args(meta=True)
    def mientras_stmt(self, hijos, meta):
        condicion = hijos[1]
        cuerpo = list(hijos[4:-2])
        return Mientras(condicion, cuerpo, meta.line, meta.column)

    # -- Declaracion de variable numerica -----------------------------------
    # var_decl: NUMERO IDENTIFIER (ASSIGN expression)? SEMICOLON

    @v_args(meta=True)
    def var_decl(self, hijos, meta):
        nombre = str(hijos[1])
        inicializador = hijos[3] if len(hijos) > 3 else None
        return DeclVar("numero", nombre, inicializador, meta.line, meta.column)

    # -- Asignacion ---------------------------------------------------------
    # assignment: lvalue ASSIGN expression SEMICOLON

    @v_args(meta=True)
    def assignment(self, hijos, meta):
        return Asignacion(hijos[0], hijos[2], meta.line, meta.column)

    # -- Lado izquierdo de asignacion ---------------------------------------
    # lvalue: IDENTIFIER | attr_access

    @v_args(meta=True)
    def lvalue(self, hijos, meta):
        hijo = hijos[0]
        if isinstance(hijo, Token) and hijo.type == "IDENTIFIER":
            return Identificador(str(hijo), meta.line, meta.column)
        return hijo  # Ya es un AccesoAtributo

    # -- Impresion ----------------------------------------------------------
    # print_stmt: IMPRIMIR expression SEMICOLON

    @v_args(meta=True)
    def print_stmt(self, hijos, meta):
        return Imprimir(hijos[1], meta.line, meta.column)

    # -- Condicion ----------------------------------------------------------
    # condition: expression relop expression

    @v_args(meta=True)
    def condition(self, hijos, meta):
        return OpBinaria(hijos[1], hijos[0], hijos[2], meta.line, meta.column)

    # -- Operador relacional ------------------------------------------------
    # relop: LT | GT | LTE | GTE | EQ | NEQ

    def relop(self, hijos):
        return str(hijos[0])

    # -- Expresiones aritmeticas (3 niveles de precedencia) -----------------

    def expression(self, hijos):
        return hijos[0]

    def addition(self, hijos):
        resultado = hijos[0]
        i = 1
        while i < len(hijos):
            operador = str(hijos[i])
            derecho = hijos[i + 1]
            linea = getattr(resultado, "linea", 0)
            col = getattr(resultado, "columna", 0)
            resultado = OpBinaria(operador, resultado, derecho, linea, col)
            i += 2
        return resultado

    def multiplication(self, hijos):
        resultado = hijos[0]
        i = 1
        while i < len(hijos):
            operador = str(hijos[i])
            derecho = hijos[i + 1]
            linea = getattr(resultado, "linea", 0)
            col = getattr(resultado, "columna", 0)
            resultado = OpBinaria(operador, resultado, derecho, linea, col)
            i += 2
        return resultado

    def unary(self, hijos):
        if len(hijos) == 1:
            return hijos[0]
        operador = str(hijos[0])
        operando = hijos[1]
        linea = operando.linea if hasattr(operando, "linea") else 0
        col = operando.columna if hasattr(operando, "columna") else 0
        return OpUnaria(operador, operando, linea, col)

    def primary(self, hijos):
        if len(hijos) == 3:
            return hijos[1]  # ( expression )
        hijo = hijos[0]
        if isinstance(hijo, Token):
            if hijo.type == "NUMBER":
                valor = float(hijo) if "." in str(hijo) else int(hijo)
                return Literal(valor, "numero", hijo.line, hijo.column)
            if hijo.type == "STRING":
                crudo = str(hijo)[1:-1]
                valor = (
                    crudo.replace("\\n", "\n")
                         .replace("\\t", "\t")
                         .replace('\\"', '"')
                         .replace("\\\\", "\\")
                )
                return Literal(valor, "cadena", hijo.line, hijo.column)
            if hijo.type == "IDENTIFIER":
                return Identificador(str(hijo), hijo.line, hijo.column)
        return hijo

    # -- Acceso a atributo --------------------------------------------------
    # attr_access: IDENTIFIER DOT (HP | ATK | DEF)
    # indices:       0          1    2

    @v_args(meta=True)
    def attr_access(self, hijos, meta):
        objeto = str(hijos[0])   # nombre del personaje
        atributo = str(hijos[2]) # "hp", "atk" o "def" (hijos[1] es el punto)
        return AccesoAtributo(objeto, atributo, meta.line, meta.column)


# ---------------------------------------------------------------------------
# Interfaz publica
# ---------------------------------------------------------------------------

_parser = None


def _crear_parser():
    """Crea el parser Lark con la gramatica del DSL TurnGame."""
    with open(RUTA_GRAMATICA, "r", encoding="utf-8") as f:
        gramatica = f.read()
    return lark.Lark(
        gramatica,
        parser="lalr",
        maybe_placeholders=True,
        propagate_positions=True,
    )


def obtener_parser():
    """Retorna el parser (singleton)."""
    global _parser
    if _parser is None:
        _parser = _crear_parser()
    return _parser


def parsear_archivo(ruta: str) -> lark.Tree:
    """Analiza un archivo .tg y retorna el arbol de Lark."""
    parser = obtener_parser()
    with open(ruta, "r", encoding="utf-8") as f:
        texto = f.read()
    return parser.parse(texto)


def parsear_linea(texto: str) -> lark.Tree:
    """Analiza una linea de texto y retorna el arbol de Lark."""
    parser = obtener_parser()
    return parser.parse(texto)


def analizar_archivo(ruta: str) -> Programa:
    """Analiza un archivo .tg y retorna el AST (Programa)."""
    arbol_lark = parsear_archivo(ruta)
    return TransformadorAST().transform(arbol_lark)


def analizar_linea(texto: str) -> NodoAST:
    """Analiza una linea de texto y retorna el nodo AST resultante."""
    arbol_lark = parsear_linea(texto)
    return TransformadorAST().transform(arbol_lark)


# Mantener compatibilidad con codigo existente
get_parser = obtener_parser
parse_file = parsear_archivo
parse_line = parsear_linea
