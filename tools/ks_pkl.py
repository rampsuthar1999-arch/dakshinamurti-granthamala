# rebuild ks/pages.pkl: bbox text for pages with Kruti text, pdfium for glyph-code pages
import sys, re, html, pickle
sys.path.insert(0, '/home/claude/work')
from kruti import convert
src = open('/home/claude/work/ks/bbox.html', encoding='utf-8').read()
pages = src.split('<page ')[1:]
P = []
for pn, pg in enumerate(pages, 1):
    ls = []
    for m in re.finditer(r'<line xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</line>', pg, re.S):
        ws = [html.unescape(w) for w in re.findall(r'<word[^>]*>(.*?)</word>', m.group(5))]
        ls.append([float(m.group(i)) for i in range(1, 5)] + [convert(' '.join(ws), tra_short=(87 <= pn <= 1115))])
    P.append(ls)
pickle.dump(P, open('/home/claude/work/ks/pages.pkl', 'wb'))
