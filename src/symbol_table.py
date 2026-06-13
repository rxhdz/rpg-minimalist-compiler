"""Tabla de símbolos con soporte para ámbitos anidados.

Estructuras:
  - SymbolEntry: almacena toda la información de una variable declarada
  - SymbolTable: pila de ámbitos, declaración y resolución de símbolos
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SymbolEntry:
    """Informacion de una variable declarada en el programa."""

    name: str
    type: str                     # "character" | "number"
    line: int = 0
    column: int = 0
    initialized: bool = False

    # Para personaje -- cada atributo tiene { "value": int, "addr": int }
    hp: dict | None = None
    atk: dict | None = None
    defense: dict | None = None
    static_hp: int | None = None   # HP rastreado estaticamente (regla D3)

    # Para numero
    addr: int | None = None
    value: Any | None = None         # valor estatico conocido (None si es runtime)

    def __repr__(self) -> str:
        if self.type == "character":
            hp_v = self.hp["value"] if self.hp else "?"
            atk_v = self.atk["value"] if self.atk else "?"
            def_v = self.defense["value"] if self.defense else "?"
            return (
                f"SymbolEntry({self.name!r}, type=character, "
                f"hp={hp_v}, atk={atk_v}, def={def_v}, "
                f"static_hp={self.static_hp})"
            )
        return (
            f"SymbolEntry({self.name!r}, type={self.type!r}, "
            f"addr={self.addr}, value={self.value}, "
            f"initialized={self.initialized})"
        )


class SymbolTable:
    """Tabla de simbolos con pila de ambitos anidados."""

    def __init__(self):
        self.scopes: list[dict[str, SymbolEntry]] = [{}]
        self.addr_counter: int = 0

    # -- Gestión de ámbitos ------------------------------------------------

    def open_scope(self):
        self.scopes.append({})

    def close_scope(self):
        self.scopes.pop()

    # -- Declaracion -------------------------------------------------------

    def declare(self, entry: SymbolEntry) -> bool:
        """Declara un simbolo en el ambito actual.

        Retorna True si se declaro correctamente.
        Retorna False si ya existe (redeclaracion en el mismo ambito).
        """
        name = entry.name
        if name in self.scopes[-1]:
            return False

        # Asignar direcciones de memoria
        if entry.type == "number":
            entry.addr = self.addr_counter
            self.addr_counter += 1
        elif entry.type == "character":
            entry.hp["addr"] = self.addr_counter
            self.addr_counter += 1
            entry.atk["addr"] = self.addr_counter
            self.addr_counter += 1
            entry.defense["addr"] = self.addr_counter
            self.addr_counter += 1

        self.scopes[-1][name] = entry
        return True

    # -- Resolucion --------------------------------------------------------

    def resolve(self, name: str) -> SymbolEntry | None:
        """Busca un simbolo en todos los ambitos (del mas interno al externo).

        Retorna la entrada si existe, None si no.
        """
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def is_declared(self, name: str) -> bool:
        return self.resolve(name) is not None

    # -- Rastreo estático de HP (regla D3) ---------------------------------

    def get_static_hp(self, name: str) -> int | None:
        entry = self.resolve(name)
        if entry and entry.type == "character":
            return entry.static_hp
        return None

    def update_static_hp(self, name: str, new_hp: int):
        entry = self.resolve(name)
        if entry and entry.type == "character":
            entry.static_hp = new_hp

    # -- Utilidades --------------------------------------------------------

    def get_type(self, name: str) -> str | None:
        entry = self.resolve(name)
        return entry.type if entry else None

    def display(self) -> str:
        """Retorna una representación legible de todos los ámbitos."""
        parts = []
        for i, scope in enumerate(self.scopes):
            parts.append(f"--- Scope {i} ---")
            for name, entry in scope.items():
                parts.append(f"  {entry}")
        return "\n".join(parts)
