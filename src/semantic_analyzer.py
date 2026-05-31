"""Análisis semántico del DSL TurnGame.

Recorre el AST y verifica:
  - Reglas generales: G1 (var no declarada), G2 (redeclaración),
    G3 (tipos incompatibles), G4 (uso antes de inicializar)
  - Reglas de dominio: D1 (hp/atk/def >= 0), D2 (atacante/víctima declarados),
    D3 (no atacar a HP <= 0), D4 (número entero >= 0)
"""

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
)
from .symbol_table import EntradaSimbolo, TablaSimbolos

PALABRAS_RESERVADAS = {
    "personaje", "hp", "atk", "def", "turno", "usar", "ataque", "en",
    "repeat", "veces", "si", "entonces", "sino", "fin",
    "mientras", "hacer", "numero", "imprimir",
}


class AnalizadorSemantico:
    """Analiza semánticamente un AST del DSL TurnGame."""

    def __init__(self):
        self.tabla = TablaSimbolos()
        self.errores: list[str] = []
        self._muertos_reportados: set[tuple[int, int]] = set()

    # ------------------------------------------------------------------
    # Punto de entrada
    # ------------------------------------------------------------------

    def analizar(self, programa: Programa) -> list[str]:
        """Analiza el AST completo y retorna la lista de errores semanticos."""
        self._visitar(programa)
        return self.errores

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------

    def _error(self, mensaje: str, linea: int, columna: int):
        self.errores.append(
            f"Error semántico [línea {linea}, columna {columna}]: {mensaje}"
        )

    def _obtener_tipo(self, nodo: NodoAST) -> str | None:
        """Determina el tipo de una expresion."""
        if isinstance(nodo, Literal):
            return nodo.tipo
        if isinstance(nodo, Identificador):
            entrada = self.tabla.resolver(nodo.nombre)
            return entrada.tipo if entrada else None
        if isinstance(nodo, AccesoAtributo):
            return "numero"
        if isinstance(nodo, OpBinaria):
            if nodo.operador in ("<", ">", "<=", ">=", "==", "!="):
                return "booleano"
            return "numero"
        if isinstance(nodo, OpUnaria):
            return self._obtener_tipo(nodo.operando)
        return None

    def _evaluar_expresion(self, nodo: NodoAST) -> tuple:
        """Intenta evaluar una expresion a un valor numérico estático.

        Retorna (valor, tipo) donde valor es int/float/None si no es reducible.
        """
        if isinstance(nodo, Literal):
            return nodo.valor, nodo.tipo
        if isinstance(nodo, Identificador):
            entrada = self.tabla.resolver(nodo.nombre)
            if entrada and entrada.tipo == "numero" and entrada.valor is not None:
                return entrada.valor, "numero"
            return None, "numero"
        if isinstance(nodo, OpUnaria):
            v, t = self._evaluar_expresion(nodo.operando)
            if v is not None and t == "numero":
                if nodo.operador == "-":
                    return -v, "numero"
                return v, "numero"
            return None, "numero"
        if isinstance(nodo, OpBinaria):
            vi, ti = self._evaluar_expresion(nodo.izquierdo)
            vd, td = self._evaluar_expresion(nodo.derecho)
            if vi is not None and vd is not None and ti == "numero" and td == "numero":
                if nodo.operador == "+":
                    return vi + vd, "numero"
                if nodo.operador == "-":
                    return vi - vd, "numero"
                if nodo.operador == "*":
                    return vi * vd, "numero"
                if nodo.operador == "/":
                    if vd != 0:
                        return vi / vd, "numero"
        return None, "numero"

    # ------------------------------------------------------------------
    # Visitor principal
    # ------------------------------------------------------------------

    def _visitar(self, nodo: NodoAST):
        if isinstance(nodo, Programa):
            self._visitar_programa(nodo)
        elif isinstance(nodo, DeclPersonaje):
            self._visitar_decl_personaje(nodo)
        elif isinstance(nodo, Turno):
            self._visitar_turno(nodo)
        elif isinstance(nodo, Repeat):
            self._visitar_repeat(nodo)
        elif isinstance(nodo, Si):
            self._visitar_si(nodo)
        elif isinstance(nodo, Mientras):
            self._visitar_mientras(nodo)
        elif isinstance(nodo, DeclVar):
            self._visitar_decl_var(nodo)
        elif isinstance(nodo, Asignacion):
            self._visitar_asignacion(nodo)
        elif isinstance(nodo, Imprimir):
            self._visitar_imprimir(nodo)
        elif isinstance(nodo, OpBinaria):
            self._visitar_op_binaria(nodo)
        elif isinstance(nodo, OpUnaria):
            self._visitar_op_unaria(nodo)
        elif isinstance(nodo, Identificador):
            self._visitar_identificador(nodo)
        elif isinstance(nodo, AccesoAtributo):
            self._visitar_atributo(nodo)

    # ------------------------------------------------------------------
    # G1 + G4: Identificador
    # ------------------------------------------------------------------

    def _visitar_identificador(self, nodo: Identificador):
        entrada = self.tabla.resolver(nodo.nombre)
        if not entrada:
            self._error(
                f"'{nodo.nombre}' no ha sido declarado.",
                nodo.linea, nodo.columna,
            )
        elif not entrada.inicializado:
            self._error(
                f"'{nodo.nombre}' se usa antes de ser inicializado.",
                nodo.linea, nodo.columna,
            )

    # ------------------------------------------------------------------
    # G1: Acceso a atributo
    # ------------------------------------------------------------------

    def _visitar_atributo(self, nodo: AccesoAtributo):
        entrada = self.tabla.resolver(nodo.objeto)
        if not entrada:
            self._error(
                f"'{nodo.objeto}' no ha sido declarado.",
                nodo.linea, nodo.columna,
            )
        elif entrada.tipo != "personaje":
            self._error(
                f"'{nodo.objeto}' no es un personaje (es '{entrada.tipo}'), "
                f"no tiene atributos.",
                nodo.linea, nodo.columna,
            )

    # ------------------------------------------------------------------
    # Programa
    # ------------------------------------------------------------------

    def _visitar_programa(self, nodo: Programa):
        for stmt in nodo.nodos:
            self._visitar(stmt)

    # ------------------------------------------------------------------
    # G2 + D1: Declaracion de personaje
    # ------------------------------------------------------------------

    def _visitar_decl_personaje(self, nodo: DeclPersonaje):
        # M1: palabras reservadas como nombre
        if nodo.nombre in PALABRAS_RESERVADAS:
            self._error(
                f"'{nodo.nombre}' es una palabra reservada y no puede "
                f"usarse como nombre de personaje.",
                nodo.linea, nodo.columna,
            )
            return

        # D1: hp, atk, def no negativos
        if nodo.hp < 0:
            self._error(
                f"'hp' de '{nodo.nombre}' es negativo ({nodo.hp}). Debe ser >= 0.",
                nodo.linea, nodo.columna,
            )
        if nodo.atk < 0:
            self._error(
                f"'atk' de '{nodo.nombre}' es negativo ({nodo.atk}). Debe ser >= 0.",
                nodo.linea, nodo.columna,
            )
        if nodo.defensa < 0:
            self._error(
                f"'def' de '{nodo.nombre}' es negativo ({nodo.defensa}). Debe ser >= 0.",
                nodo.linea, nodo.columna,
            )

        entrada = EntradaSimbolo(
            nodo.nombre, "personaje", linea=nodo.linea, columna=nodo.columna
        )
        entrada.hp = {"valor": nodo.hp, "dir": None}
        entrada.atk = {"valor": nodo.atk, "dir": None}
        entrada.defensa = {"valor": nodo.defensa, "dir": None}
        entrada.hp_estatico = nodo.hp
        entrada.inicializado = True

        if not self.tabla.declarar(entrada):
            self._error(
                f"'{nodo.nombre}' ya fue declarado en este ambito.",
                nodo.linea, nodo.columna,
            )

    # ------------------------------------------------------------------
    # D2 + D3: Turno de combate
    # ------------------------------------------------------------------

    def _visitar_turno(self, nodo: Turno):
        # D2: atacante debe estar declarado como personaje
        atacante = self.tabla.resolver(nodo.atacante)
        if not atacante:
            self._error(
                f"'{nodo.atacante}' no ha sido declarado como personaje.",
                nodo.linea, nodo.columna,
            )
        elif atacante.tipo != "personaje":
            self._error(
                f"'{nodo.atacante}' no es un personaje (es '{atacante.tipo}').",
                nodo.linea, nodo.columna,
            )

        # D2: victima debe estar declarada como personaje
        victima = self.tabla.resolver(nodo.victima)
        if not victima:
            self._error(
                f"'{nodo.victima}' no ha sido declarado como personaje.",
                nodo.linea, nodo.columna,
            )
            return
        if victima.tipo != "personaje":
            self._error(
                f"'{nodo.victima}' no es un personaje (es '{victima.tipo}').",
                nodo.linea, nodo.columna,
            )
            return

        # D3: verificar HP estático del atacante
        hp_a = atacante.hp_estatico
        if hp_a is not None and hp_a <= 0:
            clave = (nodo.linea, nodo.columna)
            if clave not in self._muertos_reportados:
                self._error(
                    f"no se puede atacar con '{nodo.atacante}': "
                    f"ya está derrotado (HP = {int(hp_a)}).",
                    nodo.linea, nodo.columna,
                )
                self._muertos_reportados.add(clave)
            return

        # D3: verificar HP estático de la víctima
        hp_v = victima.hp_estatico
        if hp_v is not None and hp_v <= 0:
            clave = (nodo.linea, nodo.columna)
            if clave not in self._muertos_reportados:
                self._error(
                    f"no se puede atacar a '{nodo.victima}': "
                    f"ya está derrotado (HP = {int(hp_v)}).",
                    nodo.linea, nodo.columna,
                )
                self._muertos_reportados.add(clave)
            return  # No actualizar HP si ya estaba muerto

        # Calcular daño y actualizar HP estático (puede ser negativo)
        if (
            atacante and atacante.tipo == "personaje"
            and victima and victima.tipo == "personaje"
        ):
            atk_a = atacante.atk["valor"]
            def_v = victima.defensa["valor"]
            danio = max(0, atk_a - def_v)
            hp_real = victima.hp_estatico - danio
            self.tabla.actualizar_hp_estatico(nodo.victima, hp_real)

    # ------------------------------------------------------------------
    # Repeat: simular N iteraciones (D3)
    # ------------------------------------------------------------------

    def _visitar_repeat(self, nodo: Repeat):
        for _ in range(nodo.veces):
            self.tabla.abrir_ambito()
            for stmt in nodo.cuerpo:
                self._visitar(stmt)
            self.tabla.cerrar_ambito()

    # ------------------------------------------------------------------
    # Si/Sino: analizar cada rama una vez (D3)
    # ------------------------------------------------------------------

    def _visitar_si(self, nodo: Si):
        self._visitar(nodo.condicion)
        tipo_cond = self._obtener_tipo(nodo.condicion)
        if tipo_cond and tipo_cond != "booleano":
            self._error(
                "La condicion del 'si' debe ser booleana, "
                f"no de tipo '{tipo_cond}'.",
                nodo.condicion.linea, nodo.condicion.columna,
            )

        self.tabla.abrir_ambito()
        for stmt in nodo.entonces:
            self._visitar(stmt)
        self.tabla.cerrar_ambito()

        if nodo.sino:
            self.tabla.abrir_ambito()
            for stmt in nodo.sino:
                self._visitar(stmt)
            self.tabla.cerrar_ambito()

    # ------------------------------------------------------------------
    # Mientras: analizar una iteracion del cuerpo (D3)
    # ------------------------------------------------------------------

    def _visitar_mientras(self, nodo: Mientras):
        self._visitar(nodo.condicion)
        tipo_cond = self._obtener_tipo(nodo.condicion)
        if tipo_cond and tipo_cond != "booleano":
            self._error(
                "La condicion del 'mientras' debe ser booleana, "
                f"no de tipo '{tipo_cond}'.",
                nodo.condicion.linea, nodo.condicion.columna,
            )

        self.tabla.abrir_ambito()
        for stmt in nodo.cuerpo:
            self._visitar(stmt)
        self.tabla.cerrar_ambito()

    # ------------------------------------------------------------------
    # G2 + D4: Declaracion de variable numero
    # ------------------------------------------------------------------

    def _visitar_decl_var(self, nodo: DeclVar):
        # M1: palabras reservadas como nombre
        if nodo.nombre in PALABRAS_RESERVADAS:
            self._error(
                f"'{nodo.nombre}' es una palabra reservada y no puede "
                f"usarse como nombre de variable.",
                nodo.linea, nodo.columna,
            )
            return

        valor_inicial = None

        if nodo.inicializador:
            self._visitar(nodo.inicializador)
            tipo_expr = self._obtener_tipo(nodo.inicializador)

            # G3: tipo de inicializador debe ser numero
            if tipo_expr and tipo_expr != "numero":
                self._error(
                    f"No se puede inicializar '{nodo.nombre}' de tipo 'numero' "
                    f"con una expresion de tipo '{tipo_expr}'.",
                    nodo.linea, nodo.columna,
                )

            # D4: evaluar estaticamente
            val, _ = self._evaluar_expresion(nodo.inicializador)
            if val is not None:
                if isinstance(val, float) and not val.is_integer():
                    self._error(
                        f"Variable 'numero' '{nodo.nombre}' debe ser entera, "
                        f"no '{val}'.",
                        nodo.linea, nodo.columna,
                    )
                elif val < 0:
                    self._error(
                        f"Variable 'numero' '{nodo.nombre}' no puede ser negativa "
                        f"(valor: {val}).",
                        nodo.linea, nodo.columna,
                    )
                else:
                    valor_inicial = int(val) if isinstance(val, float) else val

        entrada = EntradaSimbolo(
            nodo.nombre, "numero", linea=nodo.linea, columna=nodo.columna
        )
        entrada.valor = valor_inicial
        entrada.inicializado = nodo.inicializador is not None

        if not self.tabla.declarar(entrada):
            self._error(
                f"'{nodo.nombre}' ya fue declarado en este ambito.",
                nodo.linea, nodo.columna,
            )

    # ------------------------------------------------------------------
    # G1 + G3 + G4 + D4: Asignacion
    # ------------------------------------------------------------------

    def _visitar_asignacion(self, nodo: Asignacion):
        self._visitar(nodo.valor)
        tipo_val = self._obtener_tipo(nodo.valor)

        if isinstance(nodo.objetivo, Identificador):
            nombre = nodo.objetivo.nombre
            entrada = self.tabla.resolver(nombre)

            # G1: variable debe estar declarada
            if not entrada:
                self._error(
                    f"'{nombre}' no ha sido declarado.",
                    nodo.linea, nodo.columna,
                )
                return

            # G3: tipos compatibles
            if tipo_val and entrada.tipo != tipo_val:
                self._error(
                    f"No se puede asignar un valor de tipo '{tipo_val}' "
                    f"a '{nombre}' de tipo '{entrada.tipo}'.",
                    nodo.linea, nodo.columna,
                )

            # D4: si es numero, validar valor
            if entrada.tipo == "numero" and tipo_val == "numero":
                val, _ = self._evaluar_expresion(nodo.valor)
                if val is not None:
                    if isinstance(val, float) and not val.is_integer():
                        self._error(
                            f"Variable 'numero' '{nombre}' debe ser entera, "
                            f"no '{val}'.",
                            nodo.linea, nodo.columna,
                        )
                    elif val < 0:
                        self._error(
                            f"Variable 'numero' '{nombre}' no puede ser negativa "
                            f"(valor: {val}).",
                            nodo.linea, nodo.columna,
                        )

            entrada.inicializado = True

        elif isinstance(nodo.objetivo, AccesoAtributo):
            # Asignacion a hero.atk = expr
            obj = self.tabla.resolver(nodo.objetivo.objeto)
            if not obj:
                self._error(
                    f"'{nodo.objetivo.objeto}' no ha sido declarado.",
                    nodo.linea, nodo.columna,
                )
                return
            if obj.tipo != "personaje":
                self._error(
                    f"'{nodo.objetivo.objeto}' no es un personaje, "
                    f"no tiene atributos.",
                    nodo.linea, nodo.columna,
                )
                return

            # D4: validar que el valor sea numero no negativo
            if tipo_val and tipo_val != "numero":
                self._error(
                    f"El atributo '{nodo.objetivo.atributo}' es numérico, "
                    f"no se puede asignar un valor de tipo '{tipo_val}'.",
                    nodo.linea, nodo.columna,
                )

            val, _ = self._evaluar_expresion(nodo.valor)
            if val is not None and val < 0:
                self._error(
                    f"El atributo '{nodo.objetivo.atributo}' de "
                    f"'{nodo.objetivo.objeto}' no puede ser negativo "
                    f"(valor: {val}).",
                    nodo.linea, nodo.columna,
                )

            # A3: actualizar la tabla de símbolos si el valor es evaluable
            if val is not None:
                attr = nodo.objetivo.atributo
                entrada = self.tabla.resolver(nodo.objetivo.objeto)
                if entrada and entrada.tipo == "personaje":
                    if attr == "hp":
                        entrada.hp["valor"] = val
                        entrada.hp_estatico = val
                    elif attr == "atk":
                        entrada.atk["valor"] = val
                    elif attr == "def":
                        entrada.defensa["valor"] = val

    # ------------------------------------------------------------------
    # G4: Imprimir
    # ------------------------------------------------------------------

    def _visitar_imprimir(self, nodo: Imprimir):
        if not isinstance(nodo.valor, Literal) or nodo.valor.tipo != "cadena":
            self._visitar(nodo.valor)

    # ------------------------------------------------------------------
    # G1 + G3 + G4: OpBinaria
    # ------------------------------------------------------------------

    def _visitar_op_binaria(self, nodo: OpBinaria):
        self._visitar(nodo.izquierdo)
        self._visitar(nodo.derecho)

        tipo_izq = self._obtener_tipo(nodo.izquierdo)
        tipo_der = self._obtener_tipo(nodo.derecho)

        if nodo.operador in ("+", "-", "*", "/"):
            if tipo_izq and tipo_izq != "numero":
                self._error(
                    f"Operando izquierdo de '{nodo.operador}' debe ser "
                    f"numérico, no de tipo '{tipo_izq}'.",
                    nodo.izquierdo.linea, nodo.izquierdo.columna,
                )
            if tipo_der and tipo_der != "numero":
                self._error(
                    f"Operando derecho de '{nodo.operador}' debe ser "
                    f"numérico, no de tipo '{tipo_der}'.",
                    nodo.derecho.linea, nodo.derecho.columna,
                )
        elif nodo.operador in ("<", ">", "<=", ">=", "==", "!="):
            if tipo_izq and tipo_der and tipo_izq != tipo_der:
                self._error(
                    f"No se puede comparar un valor de tipo '{tipo_izq}' "
                    f"con uno de tipo '{tipo_der}'.",
                    nodo.linea, nodo.columna,
                )

    # ------------------------------------------------------------------
    # G3: OpUnaria
    # ------------------------------------------------------------------

    def _visitar_op_unaria(self, nodo: OpUnaria):
        self._visitar(nodo.operando)
        tipo_op = self._obtener_tipo(nodo.operando)
        if tipo_op and tipo_op != "numero":
            self._error(
                f"El operador '{nodo.operador}' requiere un operando numérico, "
                f"no de tipo '{tipo_op}'.",
                nodo.linea, nodo.columna,
            )


def analizar_semantica(programa: Programa) -> list[str]:
    """Funcion de conveniencia: analiza un AST y retorna los errores semanticos."""
    analizador = AnalizadorSemantico()
    return analizador.analizar(programa)
