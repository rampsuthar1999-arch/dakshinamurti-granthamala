import sys, re, pickle
sys.path.insert(0, '/home/claude/work'); sys.path.insert(0, '/home/claude/nb')
import pypdfium2 as pdfium
from ks_pdfium import page_lines
from kruti import convert
from conv import OPTS, pre, fix_narad
b = sys.argv[1]; o = OPTS[b]
pdf = pdfium.PdfDocument(f'{b}.pdf')
P = []
for i in range(len(pdf)):
    ls = []
    for x0, y0, x1, y1, raw in page_lines(pdf, i):
        txt = raw if re.search(r'[ऀ-ॿ]', raw) else convert(pre(raw, o), tra_short=o.get('tra', False))
        ls.append([x0, y0, x1, y1, fix_narad(txt.replace('त्र्च', 'ञ्च'))])
    P.append(ls)
pickle.dump(P, open(f'{b}.pkl', 'wb'))
n = sum(1 for pg in P for l in pg); bad = sum(1 for pg in P for l in pg if re.search(r'(^|\s)[ािीुूृेैोौंँ्]', l[4]))
print(b, 'lines', n, 'fragmented', bad)
