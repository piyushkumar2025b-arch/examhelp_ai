import sys
import os

path = r'utils/ai_engine.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if 'return raw["choices"][0]["message"]["content"]' in line:
        indent = line[:line.find('return')]
        new_lines.append(f'{indent}usage = raw.get("usage", {{}}).get("total_tokens", 0)\n')
        new_lines.append(f'{indent}return raw["choices"][0]["message"]["content"], usage\n')
    else:
        new_lines.append(line)

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Precision Update Applied")
