from pathlib import Path
p = Path('gerador_sei.py')
t = p.read_text(encoding='utf-8')
t = t.replace('self.theme_manager.get_color(', 'get_color_tuple(')
p.write_text(t, encoding='utf-8')
print('done')
