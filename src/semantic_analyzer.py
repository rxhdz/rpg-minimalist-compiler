"""Análisis semántico del DSL TurnGame.

Recorre el AST y verifica:
  - Reglas generales: G1 (var no declarada), G2 (redeclaración),
    G3 (tipos incompatibles), G4 (uso antes de inicializar)
  - Reglas de dominio: D1 (hp/atk/def >= 0), D2 (atacante/víctima declarados),
    D3 (no atacar a HP <= 0), D4 (número entero >= 0)
"""

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
)
from .symbol_table import SymbolEntry, SymbolTable

RESERVED_WORDS = {
    "character", "hp", "atk", "def", "turn", "use", "attack", "on",
    "repeat", "times", "if", "then", "else", "end",
    "while", "do", "number", "print",
}


class SemanticAnalyzer:
    """Analiza semánticamente un AST del DSL TurnGame."""

    def __init__(self):
        self.symbol_table = SymbolTable()
        self.errors: list[str] = []
        self._dead_reported: set[tuple[int, int]] = set()

    # ------------------------------------------------------------------
    # Punto de entrada
    # ------------------------------------------------------------------

    def analyze(self, program: Program) -> list[str]:
        """Analiza el AST completo y retorna la lista de errores semanticos."""
        self._visit(program)
        return self.errors

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------

    def _error(self, message: str, line: int, column: int):
        self.errors.append(
            f"Error semántico [línea {line}, columna {column}]: {message}"
        )

    def _get_type(self, node: ASTNode) -> str | None:
        """Determina el tipo de una expresion."""
        if isinstance(node, Literal):
            return node.type
        if isinstance(node, Identifier):
            entry = self.symbol_table.resolve(node.name)
            return entry.type if entry else None
        if isinstance(node, AttrAccess):
            return "number"
        if isinstance(node, BinaryOp):
            if node.operator in ("<", ">", "<=", ">=", "==", "!="):
                return "boolean"
            return "number"
        if isinstance(node, UnaryOp):
            return self._get_type(node.operand)
        return None

    def _evaluate_expression(self, node: ASTNode) -> tuple:
        """Intenta evaluar una expresion a un valor numérico estático.

        Retorna (valor, tipo) donde valor es int/float/None si no es reducible.
        """
        if isinstance(node, Literal):
            return node.value, node.type
        if isinstance(node, Identifier):
            entry = self.symbol_table.resolve(node.name)
            if entry and entry.type == "number" and entry.value is not None:
                return entry.value, "number"
            return None, "number"
        if isinstance(node, UnaryOp):
            v, t = self._evaluate_expression(node.operand)
            if v is not None and t == "number":
                if node.operator == "-":
                    return -v, "number"
                return v, "number"
            return None, "number"
        if isinstance(node, BinaryOp):
            vi, ti = self._evaluate_expression(node.left)
            vd, td = self._evaluate_expression(node.right)
            if vi is not None and vd is not None and ti == "number" and td == "number":
                if node.operator == "+":
                    return vi + vd, "number"
                if node.operator == "-":
                    return vi - vd, "number"
                if node.operator == "*":
                    return vi * vd, "number"
                if node.operator == "/":
                    if vd != 0:
                        return vi / vd, "number"
        return None, "number"

    # ------------------------------------------------------------------
    # Visitor principal
    # ------------------------------------------------------------------

    def _visit(self, node: ASTNode):
        if isinstance(node, Program):
            self._visit_program(node)
        elif isinstance(node, CharacterDecl):
            self._visit_character_decl(node)
        elif isinstance(node, Turn):
            self._visit_turn(node)
        elif isinstance(node, Repeat):
            self._visit_repeat(node)
        elif isinstance(node, If):
            self._visit_if(node)
        elif isinstance(node, While):
            self._visit_while(node)
        elif isinstance(node, VarDecl):
            self._visit_var_decl(node)
        elif isinstance(node, Assignment):
            self._visit_assignment(node)
        elif isinstance(node, Print):
            self._visit_print(node)
        elif isinstance(node, BinaryOp):
            self._visit_binary_op(node)
        elif isinstance(node, UnaryOp):
            self._visit_unary_op(node)
        elif isinstance(node, Identifier):
            self._visit_identifier(node)
        elif isinstance(node, AttrAccess):
            self._visit_attribute(node)

    # ------------------------------------------------------------------
    # G1 + G4: Identifier
    # ------------------------------------------------------------------

    def _visit_identifier(self, node: Identifier):
        entry = self.symbol_table.resolve(node.name)
        if not entry:
            self._error(
                f"'{node.name}' no ha sido declarado.",
                node.line, node.column,
            )
        elif not entry.initialized:
            self._error(
                f"'{node.name}' se usa antes de ser inicializado.",
                node.line, node.column,
            )

    # ------------------------------------------------------------------
    # G1: Acceso a atributo
    # ------------------------------------------------------------------

    def _visit_attribute(self, node: AttrAccess):
        entry = self.symbol_table.resolve(node.owner)
        if not entry:
            self._error(
                f"'{node.owner}' no ha sido declarado.",
                node.line, node.column,
            )
        elif entry.type != "character":
            self._error(
                f"'{node.owner}' no es un personaje (es '{entry.type}'), "
                f"no tiene atributos.",
                node.line, node.column,
            )

    # ------------------------------------------------------------------
    # Programa
    # ------------------------------------------------------------------

    def _visit_program(self, node: Program):
        for stmt in node.nodes:
            self._visit(stmt)

    # ------------------------------------------------------------------
    # G2 + D1: Declaracion de personaje
    # ------------------------------------------------------------------

    def _visit_character_decl(self, node: CharacterDecl):
        # M1: palabras reservadas como nombre
        if node.name in RESERVED_WORDS:
            self._error(
                f"'{node.name}' es una palabra reservada y no puede "
                f"usarse como nombre de personaje.",
                node.line, node.column,
            )
            return

        # D1: hp, atk, def enteros no negativos
        if isinstance(node.hp, float):
            self._error(
                f"'hp' de '{node.name}' debe ser un número entero, no {node.hp}.",
                node.line, node.column,
            )
        if isinstance(node.atk, float):
            self._error(
                f"'atk' de '{node.name}' debe ser un número entero, no {node.atk}.",
                node.line, node.column,
            )
        if isinstance(node.defense, float):
            self._error(
                f"'def' de '{node.name}' debe ser un número entero, no {node.defense}.",
                node.line, node.column,
            )
        if node.hp < 0:
            self._error(
                f"'hp' de '{node.name}' es negativo ({node.hp}). Debe ser >= 0.",
                node.line, node.column,
            )
        if node.atk < 0:
            self._error(
                f"'atk' de '{node.name}' es negativo ({node.atk}). Debe ser >= 0.",
                node.line, node.column,
            )
        if node.defense < 0:
            self._error(
                f"'def' de '{node.name}' es negativo ({node.defense}). Debe ser >= 0.",
                node.line, node.column,
            )

        entry = SymbolEntry(
            node.name, "character", line=node.line, column=node.column
        )
        entry.hp = {"value": node.hp, "addr": None}
        entry.atk = {"value": node.atk, "addr": None}
        entry.defense = {"value": node.defense, "addr": None}
        entry.static_hp = node.hp
        entry.initialized = True

        if not self.symbol_table.declare(entry):
            self._error(
                f"'{node.name}' ya fue declarado en este ambito.",
                node.line, node.column,
            )

    # ------------------------------------------------------------------
    # D2 + D3: Turno de combate
    # ------------------------------------------------------------------

    def _visit_turn(self, node: Turn):
        # D2: atacante debe estar declarado como personaje
        attacker = self.symbol_table.resolve(node.attacker)
        if not attacker:
            self._error(
                f"'{node.attacker}' no ha sido declarado como personaje.",
                node.line, node.column,
            )
        elif attacker.type != "character":
            self._error(
                f"'{node.attacker}' no es un personaje (es '{attacker.type}').",
                node.line, node.column,
            )

        # D2: victima debe estar declarada como personaje
        victim = self.symbol_table.resolve(node.victim)
        if not victim:
            self._error(
                f"'{node.victim}' no ha sido declarado como personaje.",
                node.line, node.column,
            )
            return
        if victim.type != "character":
            self._error(
                f"'{node.victim}' no es un personaje (es '{victim.type}').",
                node.line, node.column,
            )
            return

        # D3: verificar HP estático del atacante
        attacker_hp = attacker.static_hp
        if attacker_hp is not None and attacker_hp <= 0:
            key = (node.line, node.column)
            if key not in self._dead_reported:
                self._error(
                    f"no se puede atacar con '{node.attacker}': "
                    f"ya está derrotado (HP = {int(attacker_hp)}).",
                    node.line, node.column,
                )
                self._dead_reported.add(key)
            return

        # D3: verificar HP estático de la víctima
        victim_hp = victim.static_hp
        if victim_hp is not None and victim_hp <= 0:
            key = (node.line, node.column)
            if key not in self._dead_reported:
                self._error(
                    f"no se puede atacar a '{node.victim}': "
                    f"ya está derrotado (HP = {int(victim_hp)}).",
                    node.line, node.column,
                )
                self._dead_reported.add(key)
            return  # No actualizar HP si ya estaba muerto

        # Calcular daño y actualizar HP estático (puede ser negativo)
        if (
            attacker and attacker.type == "character"
            and victim and victim.type == "character"
        ):
            attacker_atk = attacker.atk["value"]
            victim_def = victim.defense["value"]
            damage = max(0, attacker_atk - victim_def)
            actual_hp = victim.static_hp - damage
            self.symbol_table.update_static_hp(node.victim, actual_hp)

    # ------------------------------------------------------------------
    # Repeat: simular N iteraciones (D3)
    # ------------------------------------------------------------------

    def _visit_repeat(self, node: Repeat):
        for _ in range(node.times):
            self.symbol_table.open_scope()
            for stmt in node.body:
                self._visit(stmt)
            self.symbol_table.close_scope()

    # ------------------------------------------------------------------
    # If/Else: analizar cada rama una vez (D3)
    # ------------------------------------------------------------------

    def _visit_if(self, node: If):
        self._visit(node.condition)
        cond_type = self._get_type(node.condition)
        if cond_type and cond_type != "boolean":
            self._error(
                "La condicion del 'si' debe ser booleana, "
                f"no de tipo '{cond_type}'.",
                node.condition.line, node.condition.column,
            )

        self.symbol_table.open_scope()
        for stmt in node.then_body:
            self._visit(stmt)
        self.symbol_table.close_scope()

        if node.else_body:
            self.symbol_table.open_scope()
            for stmt in node.else_body:
                self._visit(stmt)
            self.symbol_table.close_scope()

    # ------------------------------------------------------------------
    # While: analizar una iteracion del cuerpo (D3)
    # ------------------------------------------------------------------

    def _visit_while(self, node: While):
        self._visit(node.condition)
        cond_type = self._get_type(node.condition)
        if cond_type and cond_type != "boolean":
            self._error(
                "La condicion del 'mientras' debe ser booleana, "
                f"no de tipo '{cond_type}'.",
                node.condition.line, node.condition.column,
            )

        self.symbol_table.open_scope()
        for stmt in node.body:
            self._visit(stmt)
        self.symbol_table.close_scope()

    # ------------------------------------------------------------------
    # G2 + D4: Declaracion de variable numero
    # ------------------------------------------------------------------

    def _visit_var_decl(self, node: VarDecl):
        # M1: palabras reservadas como nombre
        if node.name in RESERVED_WORDS:
            self._error(
                f"'{node.name}' es una palabra reservada y no puede "
                f"usarse como nombre de variable.",
                node.line, node.column,
            )
            return

        initial_value = None

        if node.initializer:
            self._visit(node.initializer)
            expr_type = self._get_type(node.initializer)

            # G3: tipo de inicializador debe ser numero
            if expr_type and expr_type != "number":
                self._error(
                    f"No se puede inicializar '{node.name}' de tipo 'number' "
                    f"con una expresion de tipo '{expr_type}'.",
                    node.line, node.column,
                )
                return

            # D4: evaluar estaticamente
            val, _ = self._evaluate_expression(node.initializer)
            if val is not None:
                if isinstance(val, float) and not val.is_integer():
                    self._error(
                        f"Variable 'number' '{node.name}' debe ser entera, "
                        f"no '{val}'.",
                        node.line, node.column,
                    )
                elif val < 0:
                    self._error(
                        f"Variable 'number' '{node.name}' no puede ser negativa "
                        f"(valor: {val}).",
                        node.line, node.column,
                    )
                else:
                    initial_value = int(val) if isinstance(val, float) else val

        entry = SymbolEntry(
            node.name, "number", line=node.line, column=node.column
        )
        entry.value = initial_value
        entry.initialized = node.initializer is not None

        if not self.symbol_table.declare(entry):
            self._error(
                f"'{node.name}' ya fue declarado en este ambito.",
                node.line, node.column,
            )

    # ------------------------------------------------------------------
    # G1 + G3 + G4 + D4: Asignacion
    # ------------------------------------------------------------------

    def _visit_assignment(self, node: Assignment):
        self._visit(node.value)
        val_type = self._get_type(node.value)

        if isinstance(node.target, Identifier):
            name = node.target.name
            entry = self.symbol_table.resolve(name)

            # G1: variable debe estar declarada
            if not entry:
                self._error(
                    f"'{name}' no ha sido declarado.",
                    node.line, node.column,
                )
                return

            # G3: tipos compatibles
            if val_type and entry.type != val_type:
                self._error(
                    f"No se puede asignar un valor de tipo '{val_type}' "
                    f"a '{name}' de tipo '{entry.type}'.",
                    node.line, node.column,
                )

            # D4: si es numero, validar valor
            if entry.type == "number" and val_type == "number":
                val, _ = self._evaluate_expression(node.value)
                if val is not None:
                    if isinstance(val, float) and not val.is_integer():
                        self._error(
                            f"Variable 'number' '{name}' debe ser entera, "
                            f"no '{val}'.",
                            node.line, node.column,
                        )
                    elif val < 0:
                        self._error(
                            f"Variable 'number' '{name}' no puede ser negativa "
                            f"(valor: {val}).",
                            node.line, node.column,
                        )

            entry.initialized = True

        elif isinstance(node.target, AttrAccess):
            # Asignacion a hero.atk = expr
            obj = self.symbol_table.resolve(node.target.owner)
            if not obj:
                self._error(
                    f"'{node.target.owner}' no ha sido declarado.",
                    node.line, node.column,
                )
                return
            if obj.type != "character":
                self._error(
                    f"'{node.target.owner}' no es un personaje, "
                    f"no tiene atributos.",
                    node.line, node.column,
                )
                return

            # D4: validar que el valor sea numero no negativo
            if val_type and val_type != "number":
                self._error(
                    f"El atributo '{node.target.attribute}' es numérico, "
                    f"no se puede asignar un valor de tipo '{val_type}'.",
                    node.line, node.column,
                )

            val, _ = self._evaluate_expression(node.value)
            if val is not None and val < 0:
                self._error(
                    f"El atributo '{node.target.attribute}' de "
                    f"'{node.target.owner}' no puede ser negativo "
                    f"(valor: {val}).",
                    node.line, node.column,
                )

            # A3: actualizar la tabla de símbolos si el valor es evaluable
            if val is not None:
                attr = node.target.attribute
                entry = self.symbol_table.resolve(node.target.owner)
                if entry and entry.type == "character":
                    if attr == "hp":
                        entry.hp["value"] = val
                        entry.static_hp = val
                    elif attr == "atk":
                        entry.atk["value"] = val
                    elif attr == "def":
                        entry.defense["value"] = val

    # ------------------------------------------------------------------
    # G4: Print
    # ------------------------------------------------------------------

    def _visit_print(self, node: Print):
        if not isinstance(node.value, Literal) or node.value.type != "string":
            self._visit(node.value)

    # ------------------------------------------------------------------
    # G1 + G3 + G4: BinaryOp
    # ------------------------------------------------------------------

    def _visit_binary_op(self, node: BinaryOp):
        self._visit(node.left)
        self._visit(node.right)

        left_type = self._get_type(node.left)
        right_type = self._get_type(node.right)

        if node.operator in ("+", "-", "*", "/"):
            if left_type and left_type != "number":
                self._error(
                    f"Operando izquierdo de '{node.operator}' debe ser "
                    f"numérico, no de tipo '{left_type}'.",
                    node.left.line, node.left.column,
                )
            if right_type and right_type != "number":
                self._error(
                    f"Operando derecho de '{node.operator}' debe ser "
                    f"numérico, no de tipo '{right_type}'.",
                    node.right.line, node.right.column,
                )
        elif node.operator in ("<", ">", "<=", ">=", "==", "!="):
            if left_type and right_type and left_type != right_type:
                self._error(
                    f"No se puede comparar un valor de tipo '{left_type}' "
                    f"con uno de tipo '{right_type}'.",
                    node.line, node.column,
                )

    # ------------------------------------------------------------------
    # G3: UnaryOp
    # ------------------------------------------------------------------

    def _visit_unary_op(self, node: UnaryOp):
        self._visit(node.operand)
        op_type = self._get_type(node.operand)
        if op_type and op_type != "number":
            self._error(
                f"El operador '{node.operator}' requiere un operando numérico, "
                f"no de tipo '{op_type}'.",
                node.line, node.column,
            )


def analyze_semantics(program: Program) -> list[str]:
    """Funcion de conveniencia: analiza un AST y retorna los errores semanticos."""
    analyzer = SemanticAnalyzer()
    return analyzer.analyze(program)
