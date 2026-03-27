from pathlib import Path
p = Path('gerador_sei.py')
t = p.read_text(encoding='utf-8')
t = t.replace('from customtkinter import CTkToolTip\n', '')
p.write_text(t, encoding='utf-8')
print('ok')
