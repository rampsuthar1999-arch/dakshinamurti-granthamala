"""Parse the sanskritdocuments naishk.pdf text (pdftotext -layout) into {'c.n': [lines]} (verse lines only)."""
import re, json, sys
DEV = '०१२३४५६७८९'
def dn(s): return int(''.join(str(DEV.index(c)) for c in s))
C = '[क-ह]'

def syll(t):
    t = re.sub(r'[^ऀ-ॿ]', '', t)
    return len(re.findall(r'[अ-औ]|' + C + r'(?!्)', t))

def parse(path):
    raw = [l.strip() for l in open(path, encoding='utf-8')]
    lines = [l.replace('\u1cda', '') for l in raw if l and not re.search(r'[A-Za-z]', l) and not re.fullmatch(r'[०-९\d\s]+', l) and l != 'नैष्कर्म्यसिद्धिः']
    j = []
    for l in lines:   # re-join wrapped fragments: a bare verse number, or a tail of a few syllables
        if j and ((re.fullmatch(r'[॥।]?\s*[०-९]*\s*[॥।]', l) and not re.search(r'[०-९]\s*[॥।]\s*$', j[-1])) or (not re.search(r'[।॥]\s*$', j[-1]) and syll(l) <= 5 and not re.search(r'अध्यायः', l))):
            j[-1] = re.sub(r'\s*॥\s*$', '', j[-1].rstrip()) + ' ' + (l if l[0] in '॥।' or not re.match('[०-९]', l) else '॥ ' + l)
        else:
            j.append(l)
    lines = [re.sub(r'(?<=[\u0900-\u0963])\s+([०-९]+)\s*॥\s*$', r' ॥ \1॥', x) for x in j]
    out, ch, last = {}, 1, 0
    for i, l in enumerate(lines):
        if re.search(r'इति\s*\S*ऽध्यायः', l):
            ch += 1; last = 0; continue
        m = re.search(r'॥\s*([०-९]+)\s*[॥।]\s*$', l)
        if not m:
            continue
        n = dn(m.group(1))
        if n <= last:
            print('skip', ch, n, last, l, file=sys.stderr); continue
        if n != last + 1:
            print('gap', ch, last, n, file=sys.stderr)
        h2 = re.sub(r'\s*॥\s*[०-९]+\s*[॥।]\s*$', ' ॥', l)
        s_ = syll(h2)
        k = 2 if 13 <= s_ <= 18 else 4
        body = lines[i - k + 1:i] + [h2]
        out[f'{ch}.{n}'] = body; last = n
    return out


# reference typos where the printed book (checked against the scan OCR) has the correct reading
PATCHES = {'1.61': ('पलायते', 'पलायने'), '1.83': ('गभ्यते', 'गम्यते'), '2.8': ('कैमाश्रयौ', 'किमाश्रयौ'),
           '2.18': ('स्वदेहावयवेश्विव', 'स्वदेहावयवेष्विव'), '2.66': ('धीवृत्तिनामविक्रियः', 'धीवृत्तीनामविक्रियः'),
           '3.30': ('प्रत्यगुद्भुतपित्तस्य', 'प्रत्यगुद्भूतपित्तस्य'), '4.42': ('अन्यथागृहणतः', 'अन्यथा गृह्णतः'),
           '4.52': ('परमाथार्थनिष्ठं', 'परमार्थात्मनिष्ठं'), '4.76': ('भक्तया', 'भक्त्या')}

if __name__ == '__main__':
    R = parse(sys.argv[1])
    for k, (a, b) in PATCHES.items():
        hit = [i for i, l in enumerate(R[k]) if a in l]
        assert hit, (k, a)
        R[k][hit[0]] = R[k][hit[0]].replace(a, b)
    for c in '1234':
        ks = [k for k in R if k.startswith(c + '.')]; print(c, len(ks))
    json.dump(R, open(sys.argv[2], 'w'), ensure_ascii=False, indent=0)
