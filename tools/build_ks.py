import pickle, json, os, re, sys, html, glob, collections
sys.path.insert(0, '/home/claude/work')
from structure import parse_section, split_verses, number_slokas, page_labels, polish, dnum, VNUM

OUT = sys.argv[1] if len(sys.argv) > 1 else None
BID = 'krishna-sandesh'
P = pickle.load(open('/home/claude/work/ks/pages.pkl', 'rb'))
for _pg in P:
    for _l in _pg:
        for _ in range(2):
            _l[4] = re.sub(r'([०-९])ॉ', r'\1०', _l[4])
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
    hs = sorted(l[3] - l[1] for l in body)
    med_h = hs[len(hs) // 2] if hs else 12
    tall = lambda l: (l[3] - l[1]) > med_h * 1.3
    marked = set()
    for i, l in enumerate(body):
        dx = l[0] - base
        short = (l[2] - l[0]) < width * 0.78 or tall(l)
        if not (VNUM.search(l[4].strip()) and short and 8 <= dx <= 60):
            continue
        marked.add(i)
        j = i - 1
        while j >= 0 and i - j <= 4:
            p = body[j]; pdx = p[0] - base
            if not (8 <= pdx <= 60 and ((p[2] - p[0]) < width * 0.8 or tall(p))):
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


GITA = {1: ('अर्जुनविषादयोग', 47), 2: ('सांख्ययोग', 72), 3: ('कर्मयोग', 43), 4: ('ज्ञानकर्मसंन्यासयोग', 42),
        5: ('कर्मसंन्यासयोग', 29), 6: ('आत्मसंयमयोग', 47), 7: ('ज्ञानविज्ञानयोग', 30), 8: ('अक्षरब्रह्मयोग', 28),
        9: ('राजविद्याराजगुह्ययोग', 34), 10: ('विभूतियोग', 42), 11: ('विश्वरूपदर्शनयोग', 55), 12: ('भक्तियोग', 20),
        13: ('क्षेत्रक्षेत्रज्ञविभागयोग', 34), 14: ('गुणत्रयविभागयोग', 27), 15: ('पुरुषोत्तमयोग', 20),
        16: ('दैवासुरसम्पद्विभागयोग', 24), 17: ('श्रद्धात्रयविभागयोग', 28), 18: ('मोक्षसंन्यासयोग', 78)}
ORD = {1: 'प्रथम', 2: 'द्वितीय', 3: 'तृतीय', 4: 'चतुर्थ', 5: 'पञ्चम', 6: 'षष्ठ', 7: 'सप्तम', 8: 'अष्टम', 9: 'नवम', 10: 'दशम',
       11: 'एकादश', 12: 'द्वादश', 13: 'त्रयोदश', 14: 'चतुर्दश', 15: 'पञ्चदश', 16: 'षोडश', 17: 'सप्तदश', 18: 'अष्टादश'}
OCR_PAGES = set(list(range(1, 87)) + list(range(388, 916)) + list(range(1116, 1120)) + list(range(1664, 1674)))


def all_pages():
    pages = []
    for pn in range(1, N + 1):
        src = load_hocr(pn) if pn in OCR_PAGES else None
        ls = src if src is not None else [list(l) for l in P[pn - 1]]
        pages.append(mark_verses(ls))
    return pages


def find_starts(pages):
    """chapter start = page whose first lines carry 'ॐ'/ordinal + 'अध्याय' title."""
    starts = {}
    for pn in range(1, N + 1):
        top = ' '.join(l[4] for l in sorted(pages[pn - 1], key=lambda l: (l[1], l[0]))[:5])
        m = re.search(r'(प्रथम|द्वितीय|तृतीय|चतुर्थ|पञ्चम|पंचम|षष्ठ|सप्तम|अष्टम|नवम|दशम|दसवाँ|ग्यारहवाँ|बारहवाँ|तेरहवाँ|चौदहवाँ|चैदहवाँ|पन्द्रहवाँ|सोलहवाँ|सत्रहवाँ|अठारहवाँ)\s*अध्याय', top)
        if m:
            print('title', pn, m.group(0))
    return starts


def drop_start(body):
    k = 0
    for i, l in enumerate(body[:5]):
        if re.search(r'[।]|॥\s*[०-९]', l[4]) and 'अध्याय' not in l[4]:
            break
        if re.search(r'ॐ|ञ्च$|अध्याय|नमः|गीता|^[^\s]{0,3}$', l[4].strip()):
            k = i + 1
    return body[k:]


def build(OUT, starts):
    pages = all_pages()
    labels = page_labels(pages, 64, N)
    os.makedirs(f'{OUT}/data/{BID}', exist_ok=True)
    secs = [('bhumika', 0, 'भूमिका', 'front', 5, 6, ''), ('dhyana', 0, 'गीता-ध्यानम्', 'front', 7, 8, '')]
    chs = sorted(starts.items())
    for k, (num, a) in enumerate(chs):
        b = chs[k + 1][1] - 1 if k + 1 < len(chs) else 1663
        secs.append((f'g{num}', num, f'{ORD[num]} अध्याय : {GITA[num][0]}', 'k1' if num <= 6 else ('k2' if num <= 12 else 'k3'), a, b, GITA[num][0]))
    sections, slokas = [], []
    for sid, num, title, group, a, b, yoga in secs:
        skip = set(range(1116, 1120))
        bl = split_verses(parse_section(pages, a, b, title, header_y=64, para_dx=(8, 40), verse_dx=150, full_w=250,
                                       drop_start=drop_start if num else None, skip_pages=skip))
        found = number_slokas(bl) if num else []
        rows = []
        for blk in bl:
            x, t = blk['x'], blk['t']
            if t != 'h' and len(re.findall(r'[\u0905-\u0939]', x)) < 3:
                continue
            if t == 'v' and not blk.get('s') and re.search(r'इति\s*श्री|समाप्त|सम्पूर्ण', x) and len(x) < 260:
                t = 'e'
            x = polish(t, x)
            row = [t, blk['pg'], x]
            if blk.get('s'):
                row.append(blk['n'])
                slokas.append([num, blk['n'], len(rows), blk['pg'], x.split('\n')[0][:80]])
            elif blk.get('c'):
                row.append(0)
            if blk.get('c'):
                row.append('c')
            rows.append(row)
        meta = {'id': sid, 'num': num, 'title': title, 'group': group, 'start': a, 'end': b}
        if num:
            meta['sub'] = f'{ORD[num]} अध्याय · {GITA[num][1]} श्लोक'
        json.dump({**meta, 'blocks': rows}, open(f'{OUT}/data/{BID}/{sid}.json', 'w'), ensure_ascii=False, separators=(',', ':'))
        meta['slokas'] = len(found)
        sections.append(meta)
        if num:
            exp = GITA[num][1]
            print(sid, a, b, 'slokas', len(set(found)), '/', exp, 'missing', sorted(set(range(1, exp + 1)) - set(found))[:15])
    book = {
        'id': BID, 'title': 'श्रीकृष्ण-सन्देश', 'titleRoman': 'Śrī Kṛṣṇa Sandeśa',
        'author': 'श्रीमद्भगवद्गीता', 'commentator': 'श्री १०८ स्वामी महेशानन्द गिरि जी महाराज',
        'publisher': 'श्रीदक्षिणामूर्ति मठ प्रकाशन, वाराणसी', 'series': 'श्रीदक्षिणामूर्तिसंस्कृतग्रन्थमाला – ५८',
        'pages': N, 'imgDir': f'pages/{BID}', 'labels': labels, 'firstSection': 'g1',
        'groups': {'front': 'प्रारम्भिक', 'k1': 'प्रथम षट्क · अध्याय १–६', 'k2': 'द्वितीय षट्क · अध्याय ७–१२', 'k3': 'तृतीय षट्क · अध्याय १३–१८'},
        'secLabel': 'अध्याय', 'secAbbr': 'अ.',
        'extraPages': [{'title': 'मुखपृष्ठ', 'page': 1}, {'title': 'अध्यायक्रम', 'page': 3}],
        'sections': sections,
    }
    json.dump(book, open(f'{OUT}/data/{BID}/book.json', 'w'), ensure_ascii=False, indent=1)
    json.dump(slokas, open(f'{OUT}/data/{BID}/slokas.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    print('total slokas', len(slokas), '/ 700')


if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[2] == 'titles':
        find_starts(all_pages())
    else:
        STARTS = json.loads(sys.argv[2])
        build(OUT, {int(k): v for k, v in STARTS.items()})
