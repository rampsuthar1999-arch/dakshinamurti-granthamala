"""per-book legacy-font conversion → <book>.pkl (lines with geometry, Unicode text)"""
import sys, re, html, pickle
sys.path.insert(0, '/home/claude/work')
from kruti import convert

OPTS = {  # std: font uses StandardEncoding (’=' ‘=`); tra: '=k' means त्र; chanakya: Walkman-Chanakya glyph pieces/digits
    'bodhasara': dict(tra=True, narad=True), 'chidananda': dict(tra=True, narad=True), 'dahara': dict(std=True, tra=True),
    'purushottama': dict(std=True), 'svetaketu': dict(std=True, tra=True), 'shivasankalpa': dict(tra=True, chanakya=True),
}
CH_DIG = str.maketrans('úûüýþÿö÷øù', '0123456789')


def pre(t, o):
    if o.get('std'):
        t = t.replace('’', "'").replace('‘', '`')
    if o.get('narad'):
        t = t.replace('¯', 'fa')   # Narad: ि + ं drawn as one pre-base glyph
    if o.get('chanakya'):
        t = t.translate(CH_DIG)
        t = re.sub(r'o([qwsSz`aW¡]*)Q', r'd\1', t)   # क = व-piece + hook
        t = re.sub(r'i([qwsSz`aW¡]*)Q', r'Q\1', t)   # फ = प-piece + hook
        t = t.replace(')', '_').replace('ê', '_').replace('Í', '_')     # ऋ
        t = t.replace('/', '/k')                      # full ध (Kruti '/' is half ध्)
        t = t.replace('¼', ')')                       # द्ध
    return t


def fix_narad(t):
    # a pre-base ि+ं glyph left at the start of a word belongs after the following consonant cluster
    return re.sub(r'(^|(?<=[\s\'"‘“(\[]))िं((?:[क-ह]़?्)*[क-ह]़?)', r'\2िं', t)


def run(b):
    o = OPTS[b]
    src = open(f'{b}.bbox.html', encoding='utf-8').read()
    P = []
    for pg in src.split('<page ')[1:]:
        ls = []
        for m in re.finditer(r'<line xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</line>', pg, re.S):
            ws = [html.unescape(w) for w in re.findall(r'<word[^>]*>(.*?)</word>', m.group(5))]
            raw = ' '.join(ws)
            txt = raw if re.search(r'[\u0900-\u097F]', raw) else convert(pre(raw, o), tra_short=o.get('tra', False))
            ls.append([float(m.group(i)) for i in range(1, 5)] + [fix_narad(txt.replace('त्र्च', 'ञ्च'))])
        P.append(ls)
    pickle.dump(P, open(f'{b}.pkl', 'wb'))
    return P


if __name__ == '__main__':
    import collections
    for b in sys.argv[1:]:
        P = run(b)
        c = collections.Counter()
        for pg in P:
            for l in pg:
                c.update(re.findall(r'[^ऀ-ॿ\s‌‍।॥,.;:!?\'"‘’“”()\[\]{}\-–—=+*/%&°…❃×0-9]', l[4]))
        t = ' '.join(l[4] for pg in P for l in pg)
        print(b, 'odd', sum(c.values()), c.most_common(6), '| ईश्वर', t.count('ईश्वर'), 'के', t.count(' के '), 'वेफ', t.count('वेफ'))
