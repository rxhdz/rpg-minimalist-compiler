# TurnGame DSL — Compilador

Compilador para un lenguaje de combate por turnos estilo RPG minimalista, implementado en Python con **Lark**.

Proyecto academico de la asignatura **Compiladores**.

## Estado actual

- **Analisis lexico y sintactico** — parser LALR con Lark y construccion de AST explicita.
- **Analisis semantico** — tabla de simbolos con ambitos anidados, chequeo de tipos (G1-G4) y reglas del dominio (D1-D4).

## Uso

```bash
python main.py archivo.tg        # analizar archivo
python main.py archivo.tg --no-ast  # sin mostrar el AST
python main.py                   # modo REPL
```

## Estructura

```
src/
  parser.py           -- parser Lark + construccion de AST
  ast_nodes.py        -- definicion de nodos del AST
  symbol_table.py     -- tabla de simbolos con ambitos
  semantic_analyzer.py -- analisis semantico
  __init__.py
main.py               -- punto de entrada CLI
grammar.lark           -- gramatica EBNF
tests/                -- programas de prueba
BLUEPRINT.md           -- documentacion de arquitectura
```
