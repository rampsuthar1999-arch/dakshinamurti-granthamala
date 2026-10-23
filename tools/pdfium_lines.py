import pypdfium2 as pdfium, pypdfium2.raw as R, ctypes


def page_lines(pdf, idx, ytol=None):
    pg = pdf[idx]; H = pg.get_height(); tp = pg.get_textpage()
    n = tp.count_chars()
    ox, oy = ctypes.c_double(), ctypes.c_double()
    l, r, b, t = (ctypes.c_double() for _ in range(4))
    chars = []; seen = {}
    for i in range(n):
        if R.FPDFText_IsGenerated(tp.raw, i) == 1:
            continue
        u = R.FPDFText_GetUnicode(tp.raw, i)
        if u in (10, 13, 0xFFFE):
            continue
        R.FPDFText_GetCharOrigin(tp.raw, i, ox, oy)
        R.FPDFText_GetCharBox(tp.raw, i, l, r, b, t)
        fs = R.FPDFText_GetFontSize(tp.raw, i) or 10
        key = (u, round(ox.value * 2), round(oy.value * 2))
        if key in seen:  # fake bold: same glyph drawn twice at (almost) the same spot
            continue
        for dx in (-1, 1):
            for dy in (-1, 0, 1):
                if (u, key[1] + dx, key[2] + dy) in seen:
                    break
            else:
                continue
            break
        else:
            seen[key] = 1
            chars.append((oy.value, ox.value, chr(u), l.value, H - t.value, r.value, H - b.value, fs))
            continue
    # group by baseline
    chars.sort(key=lambda c: (-c[0], c[1]))
    lines = []
    for c in chars:
        tol = ytol or max(2.0, c[7] * 0.45)
        if lines and abs(lines[-1]['y'] - c[0]) <= tol:
            lines[-1]['c'].append(c)
        else:
            lines.append({'y': c[0], 'c': [c]})
    out = []
    for ln in lines:
        cs = sorted(ln['c'], key=lambda c: c[1])
        # split a baseline into separate runs when there is a big horizontal gap (columns / header left-right)
        runs = [[cs[0]]]
        for c in cs[1:]:
            if c[1] - runs[-1][-1][5] > 40:
                runs.append([c])
            else:
                runs[-1].append(c)
        for run in runs:
            txt = ''.join(c[2] for c in run)
            if not txt.strip():
                continue
            out.append([min(c[3] for c in run), min(c[4] for c in run), max(c[5] for c in run), max(c[6] for c in run), re_space(txt)])
    return out


def re_space(t):
    import re
    return re.sub(r'\s+', ' ', t).strip()
