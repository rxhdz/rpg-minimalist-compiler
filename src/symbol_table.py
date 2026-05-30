"""Tabla de simbolos con soporte para ambitos anidados.

Estructuras:
  - EntradaSimbolo: almacena toda la informacion de una variable declarada
  - TablaSimbolos: pila de ambitos, declaracion y resolucion de simbolos
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EntradaSimbolo:
    """Informacion de una variable declarada en el programa."""

    nombre: str
    tipo: str                     # "personaje" | "numero"
    linea: int = 0
    columna: int = 0
    inicializado: bool = False

    # Para personaje -- cada atributo tiene { "valor": int, "dir": int }
    hp: dict | None = None
    atk: dict | None = None
    def_val: dict | None = None
    hp_estatico: int | None = None   # HP rastreado estaticamente (regla D3)

    # Para numero
    dir: int | None = None
    valor: Any | None = None         # valor estatico conocido (None si es runtime)

    def __repr__(self) -> str:
        if self.tipo == "personaje":
            hp_v = self.hp["valor"] if self.hp else "?"
            atk_v = self.atk["valor"] if self.atk else "?"
            def_v = self.def_val["valor"] if self.def_val else "?"
            return (
                f"EntradaSimbolo({self.nombre!r}, tipo=personaje, "
                f"hp={hp_v}, atk={atk_v}, def={def_v}, "
                f"hp_estatico={self.hp_estatico})"
            )
        return (
            f"EntradaSimbolo({self.nombre!r}, tipo={self.tipo!r}, "
            f"dir={self.dir}, valor={self.valor}, "
            f"inicializado={self.inicializado})"
        )


class TablaSimbolos:
    """Tabla de simbolos con pila de ambitos anidados."""

    def __init__(self):
        self.ambitos: list[dict[str, EntradaSimbolo]] = [{}]
        self.contador_dir: int = 0

    # -- Gestion de ambitos ------------------------------------------------

    def push_ambito(self):
        self.ambitos.append({})

    def pop_ambito(self):
        self.ambitos.pop()

    # -- Declaracion -------------------------------------------------------

    def declarar(self, entrada: EntradaSimbolo) -> bool:
        """Declara un simbolo en el ambito actual.

        Retorna True si se declaro correctamente.
        Retorna False si ya existe (redeclaracion en el mismo ambito).
        """
        nombre = entrada.nombre
        if nombre in self.ambitos[-1]:
            return False

        # Asignar direcciones de memoria
        if entrada.tipo == "numero":
            entrada.dir = self.contador_dir
            self.contador_dir += 1
        elif entrada.tipo == "personaje":
            entrada.hp["dir"] = self.contador_dir
            self.contador_dir += 1
            entrada.atk["dir"] = self.contador_dir
            self.contador_dir += 1
            entrada.def_val["dir"] = self.contador_dir
            self.contador_dir += 1

        self.ambitos[-1][nombre] = entrada
        return True

    # -- Resolucion --------------------------------------------------------

    def resolver(self, nombre: str) -> EntradaSimbolo | None:
        """Busca un simbolo en todos los ambitos (del mas interno al externo).

        Retorna la entrada si existe, None si no.
        """
        for ambito in reversed(self.ambitos):
            if nombre in ambito:
                return ambito[nombre]
        return None

    def esta_declarado(self, nombre: str) -> bool:
        return self.resolver(nombre) is not None

    # -- Rastreo estatico de HP (regla D3) ---------------------------------

    def obtener_hp_estatico(self, nombre: str) -> int | None:
        entrada = self.resolver(nombre)
        if entrada and entrada.tipo == "personaje":
            return entrada.hp_estatico
        return None

    def actualizar_hp_estatico(self, nombre: str, nuevo_hp: int):
        entrada = self.resolver(nombre)
        if entrada and entrada.tipo == "personaje":
            entrada.hp_estatico = nuevo_hp

    # -- Utilidades --------------------------------------------------------

    def obtener_tipo(self, nombre: str) -> str | None:
        entrada = self.resolver(nombre)
        return entrada.tipo if entrada else None

    def mostrar(self) -> str:
        """Retorna una representacion legible de todos los ambitos."""
        partes = []
        for i, ambito in enumerate(self.ambitos):
            partes.append(f"--- Ambito {i} ---")
            for nombre, entrada in ambito.items():
                partes.append(f"  {entrada}")
        return "\n".join(partes)
