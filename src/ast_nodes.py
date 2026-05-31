from typing import Any


class NodoAST:
    linea: int
    columna: int

    def __init__(self, linea: int = 0, columna: int = 0):
        self.linea = linea
        self.columna = columna


class Programa(NodoAST):
    nodos: list[NodoAST]

    def __init__(self, nodos: list[NodoAST]):
        super().__init__(0, 0)
        self.nodos = nodos



class DeclPersonaje(NodoAST):
    nombre: str
    hp: int
    atk: int
    defensa: int

    def __init__(self, nombre: str, hp: int, atk: int, defensa: int,
                 linea: int = 0, columna: int = 0):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.hp = hp
        self.atk = atk
        self.defensa = defensa



class Turno(NodoAST):
    atacante: str
    victima: str

    def __init__(self, atacante: str, victima: str,
                 linea: int = 0, columna: int = 0):
        super().__init__(linea, columna)
        self.atacante = atacante
        self.victima = victima



class Repeat(NodoAST):
    veces: int
    cuerpo: list[NodoAST]

    def __init__(self, veces: int, cuerpo: list[NodoAST],
                 linea: int = 0, columna: int = 0):
        super().__init__(linea, columna)
        self.veces = veces
        self.cuerpo = cuerpo



class Si(NodoAST):
    condicion: NodoAST
    entonces: list[NodoAST]
    sino: list[NodoAST] | None

    def __init__(self, condicion: NodoAST, entonces: list[NodoAST],
                 sino: list[NodoAST] | None,
                 linea: int = 0, columna: int = 0):
        super().__init__(linea, columna)
        self.condicion = condicion
        self.entonces = entonces
        self.sino = sino



class Mientras(NodoAST):
    condicion: NodoAST
    cuerpo: list[NodoAST]

    def __init__(self, condicion: NodoAST, cuerpo: list[NodoAST],
                 linea: int = 0, columna: int = 0):
        super().__init__(linea, columna)
        self.condicion = condicion
        self.cuerpo = cuerpo



class DeclVar(NodoAST):
    tipo: str
    nombre: str
    inicializador: NodoAST | None

    def __init__(self, tipo: str, nombre: str,
                 inicializador: NodoAST | None,
                 linea: int = 0, columna: int = 0):
        super().__init__(linea, columna)
        self.tipo = tipo
        self.nombre = nombre
        self.inicializador = inicializador



class Asignacion(NodoAST):
    objetivo: NodoAST
    valor: NodoAST

    def __init__(self, objetivo: NodoAST, valor: NodoAST,
                 linea: int = 0, columna: int = 0):
        super().__init__(linea, columna)
        self.objetivo = objetivo
        self.valor = valor



class Imprimir(NodoAST):
    valor: NodoAST

    def __init__(self, valor: NodoAST,
                 linea: int = 0, columna: int = 0):
        super().__init__(linea, columna)
        self.valor = valor



class OpBinaria(NodoAST):
    operador: str
    izquierdo: NodoAST
    derecho: NodoAST

    def __init__(self, operador: str, izquierdo: NodoAST, derecho: NodoAST,
                 linea: int = 0, columna: int = 0):
        super().__init__(linea, columna)
        self.operador = operador
        self.izquierdo = izquierdo
        self.derecho = derecho



class OpUnaria(NodoAST):
    operador: str
    operando: NodoAST

    def __init__(self, operador: str, operando: NodoAST,
                 linea: int = 0, columna: int = 0):
        super().__init__(linea, columna)
        self.operador = operador
        self.operando = operando



class Literal(NodoAST):
    valor: Any
    tipo: str

    def __init__(self, valor: Any, tipo: str,
                 linea: int = 0, columna: int = 0):
        super().__init__(linea, columna)
        self.valor = valor
        self.tipo = tipo



class Identificador(NodoAST):
    nombre: str

    def __init__(self, nombre: str,
                 linea: int = 0, columna: int = 0):
        super().__init__(linea, columna)
        self.nombre = nombre



class AccesoAtributo(NodoAST):
    objeto: str
    atributo: str

    def __init__(self, objeto: str, atributo: str,
                 linea: int = 0, columna: int = 0):
        super().__init__(linea, columna)
        self.objeto = objeto
        self.atributo = atributo


def mostrar_ast(nodo: NodoAST, sangria: str = "") -> str:
    """Convierte un nodo del AST a string legible (en español)."""
    partes = []
    prefijo = f"{sangria}+- "

    if isinstance(nodo, Programa):
        partes.append(f"{prefijo}Programa")
        for n in nodo.nodos:
            partes.append(mostrar_ast(n, sangria + "|  "))
    elif isinstance(nodo, DeclPersonaje):
        partes.append(
            f"{prefijo}DeclPersonaje(nombre={nodo.nombre}, "
            f"hp={nodo.hp}, atk={nodo.atk}, def={nodo.defensa})"
        )
    elif isinstance(nodo, Turno):
        partes.append(
            f"{prefijo}Turno(atacante={nodo.atacante}, victima={nodo.victima})"
        )
    elif isinstance(nodo, Repeat):
        partes.append(f"{prefijo}Repeat(veces={nodo.veces})")
        for n in nodo.cuerpo:
            partes.append(mostrar_ast(n, sangria + "|  "))
    elif isinstance(nodo, Si):
        partes.append(f"{prefijo}Si")
        partes.append(f"{sangria}|  +- condicion:")
        partes.append(mostrar_ast(nodo.condicion, sangria + "|  |  "))
        partes.append(f"{sangria}|  +- entonces:")
        for n in nodo.entonces:
            partes.append(mostrar_ast(n, sangria + "|  |  "))
        if nodo.sino:
            partes.append(f"{sangria}|  +- sino:")
            for n in nodo.sino:
                partes.append(mostrar_ast(n, sangria + "|  |  "))
        partes.append(f"{sangria}|  +- fin")
    elif isinstance(nodo, Mientras):
        partes.append(f"{prefijo}Mientras")
        partes.append(f"{sangria}|  +- condicion:")
        partes.append(mostrar_ast(nodo.condicion, sangria + "|  |  "))
        partes.append(f"{sangria}|  +- cuerpo:")
        for n in nodo.cuerpo:
            partes.append(mostrar_ast(n, sangria + "|  |  "))
        partes.append(f"{sangria}|  +- fin")
    elif isinstance(nodo, DeclVar):
        ini = ""
        if nodo.inicializador:
            ini = f", inicializador="
            ini += mostrar_ast(nodo.inicializador, "").lstrip("+- ")
        partes.append(f"{prefijo}DeclVar(tipo={nodo.tipo}, nombre={nodo.nombre}{ini})")
    elif isinstance(nodo, Asignacion):
        partes.append(f"{prefijo}Asignacion")
        partes.append(f"{sangria}|  +- objetivo: {mostrar_ast(nodo.objetivo, '').lstrip('+- ')}")
        partes.append(f"{sangria}|  +- valor:")
        partes.append(mostrar_ast(nodo.valor, sangria + "|  |  "))
    elif isinstance(nodo, Imprimir):
        partes.append(f"{prefijo}Imprimir")
        partes.append(f"{sangria}|  +- {mostrar_ast(nodo.valor, '').lstrip('+- ')}")
    elif isinstance(nodo, OpBinaria):
        partes.append(f"{prefijo}OpBinaria({nodo.operador})")
        partes.append(f"{sangria}|  +- izquierdo:")
        partes.append(mostrar_ast(nodo.izquierdo, sangria + "|  |  "))
        partes.append(f"{sangria}|  +- derecho:")
        partes.append(mostrar_ast(nodo.derecho, sangria + "|     "))
    elif isinstance(nodo, OpUnaria):
        partes.append(f"{prefijo}OpUnaria({nodo.operador})")
        partes.append(mostrar_ast(nodo.operando, sangria + "|  "))
    elif isinstance(nodo, Literal):
        partes.append(f"{prefijo}Literal({nodo.valor!r}, tipo={nodo.tipo})")
    elif isinstance(nodo, Identificador):
        partes.append(f"{prefijo}Identificador({nodo.nombre})")
    elif isinstance(nodo, AccesoAtributo):
        partes.append(
            f"{prefijo}AccesoAtributo({nodo.objeto}.{nodo.atributo})"
        )
    else:
        partes.append(f"{prefijo}{type(nodo).__name__}")

    return "\n".join(partes)
