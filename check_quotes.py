line = open('frontend/app.py', encoding='utf-8').readlines()[380]
for i, c in enumerate(line):
    if c == '"' or ord(c) in (0x201c, 0x201d, 0x201e, 0x300c, 0x300d):
        print(f'pos {i}: U+{ord(c):04X} {repr(c)}')
