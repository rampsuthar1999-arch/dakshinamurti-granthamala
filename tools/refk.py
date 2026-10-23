"""Parse the reference Māṇḍūkya-kārikā text (sanskritdocuments kaarikaa.pdf → pdftotext) into {(prakarana, n): [line1, line2, ...]}."""
import re, json, sys
DEV = '०१२३४५६७८९'
def dn(s): return int(''.join(str(DEV.index(c)) for c in s))

def parse(path):
    lines = [l.strip() for l in open(path, encoding='utf-8')]
    lines = [l for l in lines if l and not re.search(r'[A-Za-z]', l)]
    ch, nk, nm, buf, out, started = 1, 1, 1, [], {}, False
    for l in lines:
        if 'प्रकरण' in l or 'हरिः ॐ' in l or l.startswith('इति'):
            buf = []; continue
        if 'बहिष्प्रज्ञो' in l:
            started = True; buf = []
        buf.append(l)
        m = re.search(r'॥\s*([०-९]+)\s*॥\s*$', l)
        if not m:
            continue
        n = dn(m.group(1))
        body = [re.sub(r'\s*॥\s*[०-९]+\s*॥\s*$', ' ॥', x).strip() for x in buf if len(re.findall(r'[क-ह]', x)) >= 3 and 'श्लोका भवन्ति' not in x and 'कारिकासहिता' not in x]
        body = [re.sub(r'^ॐ\s*॥\s*', '', x) for x in body]
        body = [x if re.search(r'[।॥]$', x) else x + ' ।' for x in body]
        buf = []
        if ch == 1 and (not started or (n == nm and n != nk)):
            nm = n + 1; continue
        if n == 1 and nk > 5:
            ch += 1; nk = 1
        if n == nk:
            out[(ch, n)] = body; nk = n + 1
    return out


# reference typos where the printed book has the correct reading
PATCHES = {(3, 1): ('उपासानाश्रितो', 'उपासनाश्रितो'), (4, 14): ('तैरूपवर्ण्यते', 'तैरुपवर्ण्यते'),
           (4, 41): ('विपर्यासात्धर्मांस्तत्रैव', 'विपर्यासाद्धर्मांस्तत्रैव'), (4, 46): ('विपर्यते', 'विपर्यये'),
           (4, 50): ('स्युराभासस्याविशेशतः', 'स्युराभासस्याविशेषतः'), (4, 67): ('नोच्यते', 'चोच्यते')}

if __name__ == '__main__':
    R = parse(sys.argv[1])
    for k, (a, b) in PATCHES.items():
        hit = [i for i, l in enumerate(R[k]) if a in l]
        assert hit, (k, a)
        R[k][hit[0]] = R[k][hit[0]].replace(a, b)
    for c in (1, 2, 3, 4):
        ks = sorted(n for (cc, n) in R if cc == c); print(c, len(ks), ks[-1] if ks else None)
    json.dump({f'{c}.{n}': v for (c, n), v in R.items()}, open(sys.argv[2], 'w'), ensure_ascii=False, indent=0)
