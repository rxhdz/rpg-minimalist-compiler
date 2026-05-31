# TurnGame — Compilador de un DSL de combate por turnos (RPG minimalista)

## Requisitos

- **Python** 3.10+
- **Lark** >= 0.12.0

## Instalacion

```
pip install -r requirements.txt
```

## Uso

Analizar un archivo `.tg`:

```
python main.py tests/prueba_valida.tg
```

El programa analiza el archivo en tres fases:
1. **Analisis lexico y sintactico** — construye el AST (con recuperacion de errores: reporta multiples errores sintacticos)
2. **Analisis semantico** — verifica reglas del dominio y tabla de simbolos
3. Si hay errores, los muestra y termina con codigo 1

### Opciones

- `--no-ast` — oculta la impresion del AST

Ejemplo:
```
python main.py --no-ast tests/prueba_valida.tg
```

### Modo REPL (entrada por linea de comandos)

```
python main.py
```

Escribe sentencias del DSL TurnGame una por una. El REPL solo realiza analisis
sintactico (sin validacion semantica). Escribe `salir` para terminar.

### Archivos de prueba

| Archivo | Descripcion |
|---|---|
| `tests/prueba_valida.tg` | Programa correcto en las tres fases |
| `tests/prueba_error_sintactico.tg` | Programa con error sintactico (falta `;`) |
| `tests/prueba_error_semantico.tg` | Programa con errores semanticos (D3 y D4) |

## Estructura del proyecto

```
├── grammar.lark              # Gramatica EBNF del DSL (Lark)
├── main.py                   # Punto de entrada: CLI y REPL
├── src/
│   ├── ast_nodes.py          # Clases del AST (Programa, DeclPersonaje, etc.)
│   ├── parser.py             # Parser Lark y transformacion a AST
│   ├── symbol_table.py       # Tabla de simbolos con ambitos anidados
│   └── semantic_analyzer.py  # Analisis semantico y reglas del dominio
├── tests/
│   ├── prueba_valida.tg
│   ├── prueba_error_sintactico.tg
│   └── prueba_error_semantico.tg
├── requirements.txt
└── BLUEPRINT.md              # Documentacion de arquitectura
```

## DSL TurnGame

Lenguaje para definir combates por turnos. Los personajes tienen HP, ataque
y defensa. El programa declara personajes y ejecuta turnos de combate.

### Palabras reservadas

```
personaje  hp  atk  def
turno  usar  ataque  en
repeat  veces
si  entonces  sino  fin
mientras  hacer
numero  imprimir
```

### Ejemplo basico

```
personaje hero hp=100 atk=25 def=10;
personaje goblin hp=40 atk=8 def=2;
turno hero usar ataque en goblin;
imprimir "Combate finalizado";
```
