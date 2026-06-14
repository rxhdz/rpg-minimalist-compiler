from pathlib import Path
from typing import Any

import lark
from lark import Token, v_args

from .ast_nodes import (
    ASTNode,
    Program,
    CharacterDecl,
    Turn,
    Repeat,
    If,
    While,
    VarDecl,
    Assignment,
    Print,
    BinaryOp,
    UnaryOp,
    Literal,
    Identifier,
    AttrAccess,
    show_ast,
)

GRAMMAR_PATH = Path(__file__).resolve().parent.parent / "grammar.lark"


# ---------------------------------------------------------------------------
# Transformador: convierte el arbol de Lark (lark.Tree) en AST propio
# ---------------------------------------------------------------------------

class ASTTransformer(lark.Transformer):
    """Convierte cada regla de la gramatica en su nodo AST correspondiente."""

    # -- Programa -----------------------------------------------------------

    def program(self, children):
        return Program(children)

    # -- Sentencias ---------------------------------------------------------

    def statement(self, children):
        return children[0]

    # -- Declaracion de personaje -------------------------------------------
    # stat_val: MINUS? NUMBER
    # character_decl: CHARACTER IDENTIFIER HP ASSIGN stat_val ATK ASSIGN stat_val DEF ASSIGN stat_val SEMICOLON

    def stat_val(self, children):
        if len(children) == 1:
            raw = str(children[0])
            return float(raw) if "." in raw else int(raw)
        raw = str(children[1])
        val = float(raw) if "." in raw else int(raw)
        return -val

    @v_args(meta=True)
    def character_decl(self, children, meta):
        name = str(children[1])
        hp = children[4]
        atk = children[7]
        defense = children[10]
        return CharacterDecl(name, hp, atk, defense, meta.line, meta.column)

    # -- Turno de combate ---------------------------------------------------
    # turn_stmt: TURN IDENTIFIER USE ATTACK ON IDENTIFIER SEMICOLON

    @v_args(meta=True)
    def turn_stmt(self, children, meta):
        attacker = str(children[1])
        victim = str(children[5])
        return Turn(attacker, victim, meta.line, meta.column)

    # -- Repeticion fija ----------------------------------------------------
    # repeat_stmt: REPEAT NUMBER TIMES LBRACE statement* RBRACE

    @v_args(meta=True)
    def repeat_stmt(self, children, meta):
        times = int(children[1])
        body = list(children[4:-1])
        return Repeat(times, body, meta.line, meta.column)

    # -- Condicional if/else/end --------------------------------------------
    # if_stmt: IF condition THEN LBRACE statement* RBRACE
    #          (ELSE LBRACE statement* RBRACE)? END

    @v_args(meta=True)
    def if_stmt(self, children, meta):
        condition = children[1]

        # Ubicar llaves de apertura/cierre
        open_brace_indices = [
            i for i, c in enumerate(children)
            if isinstance(c, Token) and c.type == "LBRACE"
        ]
        close_brace_indices = [
            i for i, c in enumerate(children)
            if isinstance(c, Token) and c.type == "RBRACE"
        ]

        # Bloque "then": entre la primera LBRACE y la primera RBRACE
        then_body = list(children[open_brace_indices[0] + 1:close_brace_indices[0]])

        # Bloque "else" (opcional)
        if len(close_brace_indices) > 1:
            else_body = list(children[open_brace_indices[1] + 1:close_brace_indices[1]])
        else:
            else_body = None

        return If(condition, then_body, else_body, meta.line, meta.column)

    # -- Bucle while --------------------------------------------------------
    # while_stmt: WHILE condition DO LBRACE statement* RBRACE END

    @v_args(meta=True)
    def while_stmt(self, children, meta):
        condition = children[1]
        body = list(children[4:-2])
        return While(condition, body, meta.line, meta.column)

    # -- Declaracion de variable numerica -----------------------------------
    # var_decl: NUMBER_TYPE IDENTIFIER (ASSIGN expression)? SEMICOLON

    @v_args(meta=True)
    def var_decl(self, children, meta):
        name = str(children[1])
        initializer = children[3] if len(children) > 3 else None
        return VarDecl("number", name, initializer, meta.line, meta.column)

    # -- Asignacion ---------------------------------------------------------
    # assignment: lvalue ASSIGN expression SEMICOLON

    @v_args(meta=True)
    def assignment(self, children, meta):
        return Assignment(children[0], children[2], meta.line, meta.column)

    # -- Lado izquierdo de asignacion ---------------------------------------
    # lvalue: IDENTIFIER | attr_access

    @v_args(meta=True)
    def lvalue(self, children, meta):
        child = children[0]
        if isinstance(child, Token) and child.type == "IDENTIFIER":
            return Identifier(str(child), meta.line, meta.column)
        return child  # Ya es un AttrAccess

    # -- Impresion ----------------------------------------------------------
    # print_stmt: PRINT expression SEMICOLON

    @v_args(meta=True)
    def print_stmt(self, children, meta):
        return Print(children[1], meta.line, meta.column)

    # -- Condicion ----------------------------------------------------------
    # condition: expression relop expression

    @v_args(meta=True)
    def condition(self, children, meta):
        return BinaryOp(children[1], children[0], children[2], meta.line, meta.column)

    # -- Operador relacional ------------------------------------------------
    # relop: LT | GT | LTE | GTE | EQ | NEQ

    def relop(self, children):
        return str(children[0])

    # -- Expresiones aritmeticas (3 niveles de precedencia) -----------------

    def expression(self, children):
        return children[0]

    def addition(self, children):
        result = children[0]
        i = 1
        while i < len(children):
            operator = str(children[i])
            right = children[i + 1]
            line = getattr(result, "line", 0)
            col = getattr(result, "column", 0)
            result = BinaryOp(operator, result, right, line, col)
            i += 2
        return result

    def multiplication(self, children):
        result = children[0]
        i = 1
        while i < len(children):
            operator = str(children[i])
            right = children[i + 1]
            line = getattr(result, "line", 0)
            col = getattr(result, "column", 0)
            result = BinaryOp(operator, result, right, line, col)
            i += 2
        return result

    def unary(self, children):
        if len(children) == 1:
            return children[0]
        operator = str(children[0])
        operand = children[1]
        line = operand.line if hasattr(operand, "line") else 0
        col = operand.column if hasattr(operand, "column") else 0
        return UnaryOp(operator, operand, line, col)

    def primary(self, children):
        if len(children) == 3:
            return children[1]  # ( expression )
        child = children[0]
        if isinstance(child, Token):
            if child.type == "NUMBER":
                value = float(child) if "." in str(child) else int(child)
                return Literal(value, "number", child.line, child.column)
            if child.type == "STRING":
                raw = str(child)[1:-1]
                value = (
                    raw.replace("\\n", "\n")
                         .replace("\\t", "\t")
                         .replace('\\"', '"')
                         .replace("\\\\", "\\")
                )
                return Literal(value, "string", child.line, child.column)
            if child.type == "IDENTIFIER":
                return Identifier(str(child), child.line, child.column)
        return child

    # -- Acceso a atributo --------------------------------------------------
    # attr_access: IDENTIFIER DOT (HP | ATK | DEF)
    # indices:       0          1    2

    @v_args(meta=True)
    def attr_access(self, children, meta):
        owner = str(children[0])   # nombre del personaje
        attribute = str(children[2]) # "hp", "atk" o "def" (children[1] es el punto)
        return AttrAccess(owner, attribute, meta.line, meta.column)


# ---------------------------------------------------------------------------
# Interfaz publica
# ---------------------------------------------------------------------------

_parser = None


def _create_parser():
    """Crea el parser Lark con la gramatica del DSL TurnGame."""
    with open(GRAMMAR_PATH, "r", encoding="utf-8") as f:
        grammar_text = f.read()
    return lark.Lark(
        grammar_text,
        parser="lalr",
        maybe_placeholders=True,
        propagate_positions=True,
    )


def get_parser():
    """Retorna el parser (singleton)."""
    global _parser
    if _parser is None:
        _parser = _create_parser()
    return _parser


def parse_file(path: str, on_error=None) -> lark.Tree:
    """Analiza un archivo .tg y retorna el arbol de Lark."""
    parser = get_parser()
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    return parser.parse(text, on_error=on_error)


def parse_line(text: str, on_error=None) -> lark.Tree:
    """Analiza una linea de texto y retorna el arbol de Lark."""
    parser = get_parser()
    return parser.parse(text, on_error=on_error)


def analyze_file(path: str, on_error=None) -> Program:
    """Analiza un archivo .tg y retorna el AST (Program)."""
    lark_tree = parse_file(path, on_error=on_error)
    return ASTTransformer().transform(lark_tree)


def analyze_line(text: str, on_error=None) -> ASTNode:
    """Analiza una linea de texto y retorna el nodo AST resultante."""
    lark_tree = parse_line(text, on_error=on_error)
    return ASTTransformer().transform(lark_tree)
