import lark
from pathlib import Path
import sys
sys.path.insert(0, str(Path(r'C:\Users\Rocio\Documents\!Mis archivos\.University\3. Tercer Año\2. Segundo Semestre\Compiladores\rpg-minimalist-compiler').resolve()))

from src.parser import get_parser

p = get_parser()
text = '''character hero hp=100 atk=25 def=10
turn hero use attack on goblin;
'''

def on_error(e):
    ip = e.interactive_parser
    print(f'=== on_error called ===')
    print(f'  Error token: {e.token.type}={e.token.value!r} line={e.token.line}')
    print(f'  Expected: {e.expected}')
    print(f'  Parser position: {ip.parser_state.position}')
    
    try:
        gen = ip.lexer_state.lex(ip.parser_state)
        first_token = next(gen)
        print(f'  First token from lex: {first_token.type}={first_token.value!r}')
    except Exception as ex:
        print(f'  EXCEPTION in callback: {type(ex).__name__}: {ex}')
        import traceback
        traceback.print_exc()
        return True  # Still return True to keep trying
    
    print(f'  Trying feed_token...')
    try:
        ip.parser_state.feed_token(first_token)
        print(f'  ACCEPTED')
    except lark.UnexpectedToken as ut:
        print(f'  REJECTED: expected {ut.expected}')
    
    return True

try:
    p.parse(text, on_error=on_error)
    print('Parse SUCCESS')
except Exception as e:
    print(f'Parse FAILED: {type(e).__name__}: {e}')
