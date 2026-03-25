lines = open('frontend/app.py', encoding='utf-8').readlines()
for i, line in enumerate(lines, 1):
    stripped = line.strip()
    # Find lines where inner ASCII " appear within a "-delimited string
    # Simple heuristic: count " chars, if odd number it's broken
    count = stripped.count('"')
    if count % 2 != 0 and count > 1:
        print(f'Line {i}: {stripped[:100]}')
