import pypdfium2 as pdfium, pypdfium2.raw as R, ctypes, pickle, sys
sys.path.insert(0, '/home/claude/work')
from kruti import convert, ks_shift

def page_lines(pdf, idx):
    pg = pdf[idx]; H = pg.get_height(); tp = pg.get_textpage()
    n = tp.count_chars(); lines = []; cur = []
    l, r, b, t = (ctypes.c_double() for _ in range(4))
    def push():
        if cur:
            xs = [c[1] for c in cur]; ys = [c[2] for c in cur]
            lines.append([min(xs), min(ys), max(c[3] for c in cur), max(c[4] for c in cur), ''.join(c[0] for c in cur)])
    seen = []
    for i in range(n):
        u = R.FPDFText_GetUnicode(tp.raw, i)
        gen = R.FPDFText_IsGenerated(tp.raw, i)
        if gen == 1:
            if u in (10, 13):
                push(); cur = []
            continue
        R.FPDFText_GetCharBox(tp.raw, i, l, r, b, t)
        # fake-bold text is drawn twice at a tiny offset: skip a repeat of the same glyph at ~same spot
        key = (u, l.value, b.value)
        if any(k[0] == u and abs(k[1] - l.value) < 1.2 and abs(k[2] - b.value) < 1.2 for k in seen[-400:]):
            continue
        seen.append(key)
        cur.append((chr(u), l.value, H - t.value, r.value, H - b.value))
    push()
    return lines

if __name__ == '__main__':
    pdf = pdfium.PdfDocument('/mnt/user-data/uploads/Sri_Krishna_Sandesh_Final_merged__1_.pdf')
    P = pickle.load(open('/home/claude/work/ks/pages.pkl', 'rb'))
    for pn in range(1120, 1664):
        ls = page_lines(pdf, pn - 1)
        P[pn - 1] = [[a, b, c, d, convert(ks_shift(txt))] for a, b, c, d, txt in ls]
    pickle.dump(P, open('/home/claude/work/ks/pages.pkl', 'wb'))
    print(' | '.join(l[4] for l in sorted(P[1120], key=lambda l: (l[1], l[0]))[:12]))
