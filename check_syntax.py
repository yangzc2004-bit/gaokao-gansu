import ast
try:
    ast.parse(open('frontend/app.py', encoding='utf-8').read())
    print('OK')
except SyntaxError as e:
    print(f'Error line {e.lineno}: {e.msg}')
    lines = open('frontend/app.py', encoding='utf-8').readlines()
    if e.lineno:
        print(repr(lines[e.lineno-1]))
