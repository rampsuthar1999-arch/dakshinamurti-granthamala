import pickle, json, os, re, sys, html, glob, collections
sys.path.insert(0, '/home/claude/work')
from structure import parse_section, split_verses, number_slokas, page_labels, polish, dnum, VNUM

OUT = sys.argv[1] if len(sys.argv) > 1 else None
BID = 'krishna-sandesh'
P = pickle.load(open('/home/claude/work/ks/pages.pkl', 'rb'))
N = len(P)
OCR_DIR = '/home/claude/ks/ocr'
SCALE = 300 / 72.0


def ocr_fix(t):
    t = t.replace('|', '।').replace('।।', '॥').replace('॥।', '॥').replace('।॥', '॥')
    t = re.sub(r'\s+([।॥,?!])', r'\1', t)
    return t


def load_hocr(pn):
    f = f'{OCR_DIR}/{pn}.hocr'
    if not os.path.exists(f):
        return None
    src = open(f, encoding='utf-8').read()
    lines = []
    for m in re.finditer(r"<span class='ocr_(?:line|header|caption|textfloat)'[^>]*title=\"bbox (\d+) (\d+) (\d+) (\d+)[^\"]*\"[^>]*>(.*?)</span>\s*(?=<span class='ocr_|</p>)", src, re.S):
        words = [html.unescape(re.sub(r'<[^>]+>', '', w)) for w in re.findall(r"<span class='ocrx_word'[^>]*>(.*?)</span>", m.group(5), re.S)]
        txt = ocr_fix(' '.join(w for w in words if w.strip()))
        if txt.strip():
            x0, y0, x1, y1 = (int(m.group(i)) / SCALE for i in range(1, 5))
            lines.append([x0, y0, x1, y1, txt])
    return lines


def mark_verses(lines):
    """Ślokas here are bold short lines starting at the paragraph indent (not centred).
    Shift them right so the generic parser treats them as verse lines."""
    ls = sorted(lines, key=lambda l: (l[1], l[0]))
    body = [l for l in ls if l[1] > 75]
    if not body:
        return ls
    full = [round(l[0]) for l in body if l[2] - l[0] > 250]
    base = collections.Counter(full).most_common(1)[0][0] if full else min(round(l[0]) for l in body)
    right = max(l[2] for l in body)
    width = right - base
    idx = {id(l): i for i, l in enumerate(body)}
    marked = set()
    for i, l in enumerate(body):
        dx = l[0] - base
        short = (l[2] - l[0]) < width * 0.78
        if not (VNUM.search(l[4].strip()) and short and 8 <= dx <= 60):
            continue
        marked.add(i)
        j = i - 1
        while j >= 0 and i - j <= 4:
            p = body[j]; pdx = p[0] - base
            if not (8 <= pdx <= 60 and (p[2] - p[0]) < width * 0.8):
                break
            if VNUM.search(p[4].strip()) or re.search(r'[—\-:?]\s*$', p[4].strip()):
                break
            if re.search(r'(^|\s)(है|हैं|में|के|की|का|से|नहीं|क्या|को|यह|भी|और|तो|कि|हो|था|थे|गया)(\s|$|[।,?!])', p[4]):
                break
            marked.add(j)
            if 'उवाच' in p[4] or 'उवाच' in p[4].replace(' ', ''):
                break
            j -= 1
    for i in marked:
        body[i][0] += 200
    return ls


if __name__ == '__main__':
    # quick test on a text page
    for pn in [94, 111, 1235]:
        ls = mark_verses([list(l) for l in P[pn - 1]])
        for l in ls:
            if l[0] > 200:
                print(pn, round(l[0]), l[4][:70])
