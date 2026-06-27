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
    "character", "hp", "mp", "mp_regen", "atk", "def", "turn", "use", "on",
    "repeat", "times", "if", "then", "else", "end",
    "while", "do", "number", "print",
}

SKILLS = {
    "attack":        {"cost": 0,  "damage": 0,     "mp_recovery_mult": 0, "effect": None},
    "fireball":      {"cost": 15, "damage": 40,    "mp_recovery_mult": 0, "effect": None},
    "ice_spike":     {"cost": 10, "damage": 25,    "mp_recovery_mult": 0, "effect": None},
    "heal":          {"cost": 20, "damage": -30,   "mp_recovery_mult": 0, "effect": None},
    "meditate":      {"cost": 0,  "damage": 0,     "mp_recovery_mult": 0.5, "effect": None},
    "poison_strike": {"cost": 12, "damage": 15,    "mp_recovery_mult": 0,
                      "effect": {"type": "poison",     "dmg_per_turn": 5, "turns": 3}},
    "shield_bash":   {"cost": 8,  "damage": 10,    "mp_recovery_mult": 0,
                      "effect": {"type": "defense_up", "multiplier": 2,  "turns": 2}},
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
        """Determina el tipo de una expresion.

        Retorna "boolean" solo para expresiones relacionales
        (>, <, ==, !=, etc.). Este tipo NO se almacena en la tabla
        de simbolos: no existen variables ni literales booleanos
        en el DSL. Se usa unicamente para validar condiciones
        de 'si' y 'mientras'.
        """
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
                    self._error(
                        "Division por cero en expresion estatica.",
                        node.line, node.column,
                    )
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

        # D1: mp entero no negativo (si está presente)
        if node.mp is not None:
            if isinstance(node.mp, float):
                self._error(
                    f"'mp' de '{node.name}' debe ser un número entero, no {node.mp}.",
                    node.line, node.column,
                )
            elif node.mp < 0:
                self._error(
                    f"'mp' de '{node.name}' es negativo ({node.mp}). Debe ser >= 0.",
                    node.line, node.column,
                )

        # D1: mp_regen entero no negativo (si está presente)
        if node.mp_regen is not None:
            if isinstance(node.mp_regen, float):
                self._error(
                    f"'mp_regen' de '{node.name}' debe ser un número entero, "
                    f"no {node.mp_regen}.",
                    node.line, node.column,
                )
            elif node.mp_regen < 0:
                self._error(
                    f"'mp_regen' de '{node.name}' es negativo ({node.mp_regen}). "
                    f"Debe ser >= 0.",
                    node.line, node.column,
                )

        entry = SymbolEntry(
            node.name, "character", line=node.line, column=node.column
        )
        entry.hp = {"value": node.hp, "addr": None}
        entry.atk = {"value": node.atk, "addr": None}
        entry.defense = {"value": node.defense, "addr": None}
        entry.static_hp = node.hp
        entry.max_mp = node.mp
        entry.static_mp = node.mp
        entry.mp_regen = (
            node.mp_regen if node.mp_regen is not None
            else (round(node.mp * 0.1) if node.mp is not None else 0)
        )
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
            return
        elif attacker.type != "character":
            self._error(
                f"'{node.attacker}' no es un personaje (es '{attacker.type}').",
                node.line, node.column,
            )
            return

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

        # D2: validar que la skill existe
        skill_name = node.skill
        if skill_name not in SKILLS:
            self._error(
                f"'{skill_name}' no es una habilidad valida.",
                node.line, node.column,
            )
            return
        skill = SKILLS[skill_name]

        # D2: si la skill tiene costo, el atacante debe tener mana
        if skill["cost"] > 0 and (attacker.max_mp is None or attacker.max_mp <= 0):
            self._error(
                f"'{node.attacker}' no tiene mana para usar "
                f"'{skill_name}' (cuesta {skill['cost']}).",
                node.line, node.column,
            )
            return

        # D3: solo simular si ambos son personajes
        if attacker.type == "character" and victim.type == "character":

            # 1. MP regen del atacante
            if attacker.max_mp is not None:
                new_mp = min(
                    attacker.max_mp,
                    attacker.static_mp + attacker.mp_regen,
                )
                self.symbol_table.update_static_mp(node.attacker, new_mp)

            # 2. Tick de efectos en atacante y víctima
            self._tick_effects(attacker)
            self._tick_effects(victim)

            # 3. Verificar HP del atacante
            if attacker.static_hp is not None and attacker.static_hp <= 0:
                self._error(
                    f"no se puede atacar con '{node.attacker}': "
                    f"ya está derrotado.",
                    node.line, node.column,
                )
                return

            # 4. Verificar HP de la víctima
            if victim.static_hp is not None and victim.static_hp <= 0:
                self._error(
                    f"no se puede atacar a '{node.victim}': "
                    f"ya está derrotado.",
                    node.line, node.column,
                )
                return

            # 5. Verificar MP suficiente
            if skill["cost"] > 0 and attacker.static_mp is not None:
                if attacker.static_mp < skill["cost"]:
                    self._error(
                        f"'{node.attacker}' no tiene suficiente mana "
                        f"(tiene {attacker.static_mp}, "
                        f"necesita {skill['cost']}).",
                        node.line, node.column,
                    )
                    return

            # --- Ejecutar skill ---

            # Descontar costo de mana
            if skill["cost"] > 0 and attacker.static_mp is not None:
                self.symbol_table.update_static_mp(
                    node.attacker, attacker.static_mp - skill["cost"]
                )

            # Recuperar mana porcentual (meditate)
            recovery_mult = skill.get("mp_recovery_mult", 0)
            if recovery_mult > 0 and attacker.max_mp is not None:
                recovery = round(attacker.max_mp * recovery_mult)
                new_mp = min(
                    attacker.max_mp,
                    attacker.static_mp + recovery,
                )
                self.symbol_table.update_static_mp(node.attacker, new_mp)

            # Calcular daño o curación
            if skill["damage"] < 0:
                # Curación: no revive, no supera HP original
                if victim.static_hp is not None and victim.static_hp > 0:
                    heal_amount = -skill["damage"]
                    new_hp = min(
                        victim.static_hp + heal_amount,
                        victim.hp["value"],
                    )
                else:
                    new_hp = victim.static_hp
            else:
                # Defensa afectada por efectos
                effective_def = victim.defense["value"]
                if "defense_up" in victim.status_effects:
                    effective_def *= victim.status_effects["defense_up"]["multiplier"]
                damage = max(0, attacker.atk["value"] + skill["damage"] - effective_def)
                new_hp = victim.static_hp - damage if victim.static_hp is not None else 0

            if new_hp is not None:
                new_hp = max(0, new_hp)
                self.symbol_table.update_static_hp(node.victim, new_hp)

            # Aplicar efecto de la skill
            if skill["effect"]:
                eff = skill["effect"]
                target = victim.status_effects
                if eff["type"] == "poison":
                    if "poison" not in target:
                        target["poison"] = {
                            "dmg_per_turn": eff["dmg_per_turn"],
                            "remaining": 0,
                        }
                    target["poison"]["remaining"] += eff["turns"]
                elif eff["type"] == "defense_up":
                    if "defense_up" not in target:
                        target["defense_up"] = {
                            "multiplier": eff["multiplier"],
                            "remaining": 0,
                        }
                    target["defense_up"]["remaining"] += eff["turns"]

    def _tick_effects(self, entry: SymbolEntry):
        """Aplica daño de efectos activos y reduce contadores (D3)."""
        for eff_name in list(entry.status_effects.keys()):
            eff = entry.status_effects[eff_name]
            if eff_name == "poison":
                if entry.static_hp is not None:
                    entry.static_hp -= eff["dmg_per_turn"]
                    if entry.static_hp < 0:
                        entry.static_hp = 0
            eff["remaining"] -= 1
            if eff["remaining"] <= 0:
                del entry.status_effects[eff_name]

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
            if val is not None:
                if isinstance(val, float) and not val.is_integer():
                    self._error(
                        f"El atributo '{node.target.attribute}' de "
                        f"'{node.target.owner}' debe ser entero, "
                        f"no '{val}'.",
                        node.line, node.column,
                    )
                elif val < 0:
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
                    elif attr == "mp":
                        entry.max_mp = val

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
