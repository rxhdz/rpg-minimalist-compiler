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
python main.py tests/valid_test.tg
```

El programa analiza el archivo en tres fases:
1. **Analisis lexico y sintactico** — construye el AST (con recuperacion de errores: reporta multiples errores sintacticos)
2. **Analisis semantico** — verifica reglas del dominio y tabla de simbolos
3. Si hay errores, los muestra y termina con codigo 1

### Opciones

- `--no-ast` — oculta la impresion del AST

Ejemplo:
```
python main.py --no-ast tests/valid_test.tg
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
| `tests/valid_test.tg` | Programa correcto en las tres fases |
| `tests/test_sintatic_error.tg` | Programa con error sintactico (falta `;`) |
| `tests/test_semantic_error.tg` | Programa con errores semanticos (D3 y D4) |
| `tests/test_multi_errors.tg` | Programa con multiples errores sintacticos |
| `tests/test_comments.tg` | Programa con comentarios de linea y bloque |
| `tests/test_skill_effects.tg` | Programa con skills, mana y efectos de estado |

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
│   ├── valid_test.tg
│   ├── test_sintatic_error.tg
│   ├── test_semantic_error.tg
│   ├── test_multi_errors.tg
│   ├── test_comments.tg
│   └── test_skill_effects.tg
├── requirements.txt
└── BLUEPRINT.md              # Documentacion de arquitectura
```

## DSL TurnGame

Lenguaje para definir combates por turnos. Los personajes tienen HP, mana (MP),
ataque y defensa. El programa declara personajes, ejecuta turnos de combate
usando habilidades con costos de mana y efectos de estado.

### Palabras reservadas

```
character  hp  mp  mp_regen  atk  def
turn  use  on
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
character <nombre> hp=<valor> atk=<valor> def=<valor> [mp=<valor>] [mp_regen=<valor>];
```

Ejemplos:
```
character hero hp=100 atk=25 def=10;
character mage hp=80 atk=15 def=5 mp=40 mp_regen=5;
```

- `mp` (opcional): puntos de mana del personaje. Si se omite, el personaje no
  tiene mana y no puede usar habilidades con costo.
- `mp_regen` (opcional): mana recuperado por turno. Si se omite pero se define
  `mp`, el valor por defecto es el 10% del mana base (redondeado).

### Turno de combate

```
turn <atacante> use <habilidad> on <victima>;
```

Ejemplos:
```
turn hero use attack on goblin;
turn mage use fireball on goblin;
```

Mecanica de combate:
- El daño base es `max(0, atk - def)`. Algunas habilidades añaden daño extra.
- Si la habilidad tiene costo de mana, se descuenta del mana del atacante.
- Si el atacante no tiene mana suficiente, el turno falla (error semantico).
- Antes de cada turno, el atacante recupera mana pasivo (`mp_regen`).
- El HP de un personaje no puede bajar de 0 ni superar su valor original.
- Si el HP llega a 0, el personaje no puede atacar ni ser atacado.
- La curacion no revive personajes con HP = 0.

### Habilidades disponibles

| Habilidad | Costo MP | Daño | Efecto |
|---|---|---|---|
| `attack` | 0 | 0 (solo atk - def) | — |
| `fireball` | 15 | 40 | — |
| `ice_spike` | 10 | 25 | — |
| `heal` | 20 | -30 (curacion) | — |
| `meditate` | 0 | 0 | Recupera 50% del mana maximo |
| `poison_strike` | 12 | 15 | Veneno: 5 de daño por turno, 3 turnos |
| `shield_bash` | 8 | 10 | Defensa duplicada por 2 turnos |

Notas:
- `attack` no requiere mana y causa solo `atk - def` (comportamiento original).
- Los efectos de estado se apilan: aplicar veneno nuevamente suma turnos.
- Los efectos se reducen al inicio de cada turno (tick).
- `defense_up` duplica la defensa del objetivo durante su duracion.

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
hero.mp = hero.mp + 10;
```

### Lectura de atributos

```
<personaje>.hp
<personaje>.mp
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
character hero hp=100 atk=25 def=10 mp=50;
character mage hp=80 atk=15 def=5 mp=40;
character goblin hp=60 atk=8 def=2;
character boss hp=150 atk=20 def=8;

turn mage use fireball on goblin;
turn mage use meditate on mage;

turn boss use attack on hero;
turn mage use heal on hero;

turn hero use poison_strike on boss;
turn hero use poison_strike on boss;

turn hero use attack on boss;
turn goblin use attack on boss;

print "Combate finalizado";
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
| D1 | HP, MP, MP_REGEN, ATK y DEF de personaje deben ser enteros >= 0 |
| D2 | Atacante y victima deben estar declarados como personaje; la habilidad debe existir; si tiene costo, el atacante debe tener mana |
| D3 | No se puede atacar con un personaje con HP <= 0, ni a un personaje con HP <= 0; se simula regeneracion de mana, tick de efectos y consumo de recursos |
| D4 | Las variables de tipo `number` deben ser enteras no negativas |
