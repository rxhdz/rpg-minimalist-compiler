from typing import Any


class ASTNode:
    line: int
    column: int

    def __init__(self, line: int = 0, column: int = 0):
        self.line = line
        self.column = column


class Program(ASTNode):
    nodes: list[ASTNode]

    def __init__(self, nodes: list[ASTNode]):
        super().__init__(0, 0)
        self.nodes = nodes



class CharacterDecl(ASTNode):
    name: str
    hp: int
    atk: int
    defense: int

    def __init__(self, name: str, hp: int, atk: int, defense: int,
                 line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.name = name
        self.hp = hp
        self.atk = atk
        self.defense = defense



class Turn(ASTNode):
    attacker: str
    victim: str

    def __init__(self, attacker: str, victim: str,
                 line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.attacker = attacker
        self.victim = victim



class Repeat(ASTNode):
    times: int
    body: list[ASTNode]

    def __init__(self, times: int, body: list[ASTNode],
                 line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.times = times
        self.body = body



class If(ASTNode):
    condition: ASTNode
    then_body: list[ASTNode]
    else_body: list[ASTNode] | None

    def __init__(self, condition: ASTNode, then_body: list[ASTNode],
                 else_body: list[ASTNode] | None,
                 line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.condition = condition
        self.then_body = then_body
        self.else_body = else_body



class While(ASTNode):
    condition: ASTNode
    body: list[ASTNode]

    def __init__(self, condition: ASTNode, body: list[ASTNode],
                 line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.condition = condition
        self.body = body



class VarDecl(ASTNode):
    type: str
    name: str
    initializer: ASTNode | None

    def __init__(self, type: str, name: str,
                 initializer: ASTNode | None,
                 line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.type = type
        self.name = name
        self.initializer = initializer



class Assignment(ASTNode):
    target: ASTNode
    value: ASTNode

    def __init__(self, target: ASTNode, value: ASTNode,
                 line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.target = target
        self.value = value



class Print(ASTNode):
    value: ASTNode

    def __init__(self, value: ASTNode,
                 line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.value = value



class BinaryOp(ASTNode):
    operator: str
    left: ASTNode
    right: ASTNode

    def __init__(self, operator: str, left: ASTNode, right: ASTNode,
                 line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.operator = operator
        self.left = left
        self.right = right



class UnaryOp(ASTNode):
    operator: str
    operand: ASTNode

    def __init__(self, operator: str, operand: ASTNode,
                 line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.operator = operator
        self.operand = operand



class Literal(ASTNode):
    value: Any
    type: str

    def __init__(self, value: Any, type: str,
                 line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.value = value
        self.type = type



class Identifier(ASTNode):
    name: str

    def __init__(self, name: str,
                 line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.name = name



class AttrAccess(ASTNode):
    owner: str
    attribute: str

    def __init__(self, owner: str, attribute: str,
                 line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.owner = owner
        self.attribute = attribute


def show_ast(node: ASTNode, indent: str = "") -> str:
    """Convierte un nodo del AST a string legible (en español)."""
    parts = []
    prefix = f"{indent}+- "

    if isinstance(node, Program):
        parts.append(f"{prefix}Program")
        for n in node.nodes:
            parts.append(show_ast(n, indent + "|  "))
    elif isinstance(node, CharacterDecl):
        parts.append(
            f"{prefix}CharacterDecl(name={node.name}, "
            f"hp={node.hp}, atk={node.atk}, def={node.defense})"
        )
    elif isinstance(node, Turn):
        parts.append(
            f"{prefix}Turn(attacker={node.attacker}, victim={node.victim})"
        )
    elif isinstance(node, Repeat):
        parts.append(f"{prefix}Repeat(times={node.times})")
        for n in node.body:
            parts.append(show_ast(n, indent + "|  "))
    elif isinstance(node, If):
        parts.append(f"{prefix}If")
        parts.append(f"{indent}|  +- condition:")
        parts.append(show_ast(node.condition, indent + "|  |  "))
        parts.append(f"{indent}|  +- then:")
        for n in node.then_body:
            parts.append(show_ast(n, indent + "|  |  "))
        if node.else_body:
            parts.append(f"{indent}|  +- else:")
            for n in node.else_body:
                parts.append(show_ast(n, indent + "|  |  "))
        parts.append(f"{indent}|  +- end")
    elif isinstance(node, While):
        parts.append(f"{prefix}While")
        parts.append(f"{indent}|  +- condition:")
        parts.append(show_ast(node.condition, indent + "|  |  "))
        parts.append(f"{indent}|  +- body:")
        for n in node.body:
            parts.append(show_ast(n, indent + "|  |  "))
        parts.append(f"{indent}|  +- end")
    elif isinstance(node, VarDecl):
        ini = ""
        if node.initializer:
            ini = f", initializer="
            ini += show_ast(node.initializer, "").lstrip("+- ")
        parts.append(f"{prefix}VarDecl(type={node.type}, name={node.name}{ini})")
    elif isinstance(node, Assignment):
        parts.append(f"{prefix}Assignment")
        parts.append(f"{indent}|  +- target: {show_ast(node.target, '').lstrip('+- ')}")
        parts.append(f"{indent}|  +- value:")
        parts.append(show_ast(node.value, indent + "|  |  "))
    elif isinstance(node, Print):
        parts.append(f"{prefix}Print")
        parts.append(f"{indent}|  +- {show_ast(node.value, '').lstrip('+- ')}")
    elif isinstance(node, BinaryOp):
        parts.append(f"{prefix}BinaryOp({node.operator})")
        parts.append(f"{indent}|  +- left:")
        parts.append(show_ast(node.left, indent + "|  |  "))
        parts.append(f"{indent}|  +- right:")
        parts.append(show_ast(node.right, indent + "|     "))
    elif isinstance(node, UnaryOp):
        parts.append(f"{prefix}UnaryOp({node.operator})")
        parts.append(show_ast(node.operand, indent + "|  "))
    elif isinstance(node, Literal):
        parts.append(f"{prefix}Literal({node.value!r}, type={node.type})")
    elif isinstance(node, Identifier):
        parts.append(f"{prefix}Identifier({node.name})")
    elif isinstance(node, AttrAccess):
        parts.append(
            f"{prefix}AttrAccess({node.owner}.{node.attribute})"
        )
    else:
        parts.append(f"{prefix}{type(node).__name__}")

    return "\n".join(parts)
