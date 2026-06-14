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
│   ├── ast_nodes.py          # Clases del AST (Program, CharacterDecl, etc.)
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
character  hp  atk  def
turn  use  attack  on
repeat  times
if  then  else  end
while  do
number  print
```

### Tipos de datos

- `number` — numeros enteros no negativos
- `string` — cadenas de texto (solamente en `print`)
- `boolean` — resultado de comparaciones (`==`, `!=`, `<`, `>`, `<=`, `>=`)

### Declaracion de personaje

```
character <nombre> hp=<valor> atk=<valor> def=<valor>;
```

Ejemplo:
```
character hero hp=100 atk=25 def=10;
```

### Turno de combate

```
turn <atacante> use attack on <victima>;
```

Ejemplo:
```
turn hero use attack on goblin;
```

Mecanica de combate:
- El atacante causa `max(0, atk - def)` de daño a la victima
- El HP de la victima se reduce en esa cantidad
- Si el HP de un personaje llega a 0 o menos, no puede atacar ni ser atacado

### Asignacion

```
<variable> = <expresion>;
<personaje>.<atributo> = <expresion>;
```

Ejemplos:
```
number danio_extra = 10;
hero.atk = hero.atk + danio_extra;
goblin.hp = goblin.hp - 5;
```

### Lectura de atributos

```
<personaje>.hp
<personaje>.atk
<personaje>.def
```

### Condicional if

```
if <condicion> then {
    ...
} else {
    ...
} end
```

La rama `else` es opcional.

### Bucle repeat

```
repeat <N> times {
    ...
}
```

Ejecuta el cuerpo `N` veces.

### Bucle while

```
while <condicion> do {
    ...
} end
```

### Impresion

```
print <expresion>;
print "texto literal";
```

### Expresiones

Soportan los operadores aritmeticos `+`, `-`, `*`, `/` (con precedencia estandar)
y parentesis `(`, `)`. Las condiciones usan los operadores relacionales
`==`, `!=`, `<`, `>`, `<=`, `>=`.

### Variables numericas

```
number <nombre> = <expresion>;
number <nombre>;
```

Deben ser enteros no negativos. La inicializacion es opcional.

### Ejemplo completo

```
character hero hp=100 atk=25 def=10;
character goblin hp=40 atk=8 def=2;
character boss hp=200 atk=15 def=5;

turn hero use attack on goblin;
turn goblin use attack on hero;

number danio_extra = 10;
hero.atk = hero.atk + danio_extra;

if goblin.hp > 0 then {
    turn hero use attack on goblin;
} else {
    print "Goblin derrotado";
} end

repeat 2 times {
    turn hero use attack on boss;
}

while hero.hp > 0 do {
    number ronda = 1;
    turn hero use attack on boss;
    ronda = ronda + 1;
} end

print "Combate finalizado";
print hero.hp;
```

## Reglas semanticas

### Reglas generales

| Regla | Descripcion |
|---|---|
| G1 | Toda variable debe ser declarada antes de usarse |
| G2 | No se puede redeclarar una variable en el mismo ambito |
| G3 | Los tipos deben ser compatibles en asignaciones y operaciones |
| G4 | No se puede usar una variable antes de ser inicializada |

### Reglas de dominio

| Regla | Descripcion |
|---|---|
| D1 | HP, ATK y DEF de personaje deben ser >= 0 |
| D2 | Atacante y victima deben estar declarados como personaje |
| D3 | No se puede atacar con un personaje con HP <= 0, ni a un personaje con HP <= 0 |
| D4 | Las variables de tipo `number` deben ser enteras no negativas |
