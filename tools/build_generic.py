"""Build app data for the additional books (legacy-font conversions and OCR)."""
import pickle, json, os, re, sys, collections, html, glob
sys.path.insert(0, '/home/claude/work'); sys.path.insert(0, '/home/claude/nb')
from structure import parse_section, split_verses, number_slokas, page_labels, polish, dnum, VNUM
from pravachan import pnum

NB = '/home/claude/nb'
OUT = '/home/claude/dakshinamurti-granthamala'
D2 = str.maketrans('0123456789', '०१२३४५६७८९')
COMM = 'श्री १०८ स्वामी महेशानन्द गिरि जी महाराज'
PUB = 'श्रीदक्षिणामूर्ति मठ प्रकाशन, वाराणसी'


# ---------------------------------------------------------------- sources
def load_pkl(b):
    return pickle.load(open(f'{NB}/{b}.pkl', 'rb'))


def load_ocr(d, n, scale=300 / 72.0):
    sys.path.insert(0, '/home/claude/work')
    from build_ks import ocr_fix
    P = []
    for pn in range(1, n + 1):
        f = f'/home/claude/ocrq/{d}/{pn}.hocr'
        ls = []
        if os.path.exists(f):
            src = open(f, encoding='utf-8').read()
            for m in re.finditer(r"<span class='ocr_(?:line|header|caption|textfloat)'[^>]*title=\"bbox (\d+) (\d+) (\d+) (\d+)[^\"]*\"[^>]*>(.*?)</span>\s*(?=<span class='ocr_|</p>)", src, re.S):
                words = [html.unescape(re.sub(r'<[^>]+>', '', w)) for w in re.findall(r"<span class='ocrx_word'[^>]*>(.*?)</span>", m.group(5), re.S)]
                txt = ocr_fix(' '.join(w for w in words if w.strip()))
                if txt.strip():
                    ls.append([int(m.group(i)) / scale for i in range(1, 5)] + [txt])
        P.append(ls)
    return P


def fix_text(t, cfg):
    t = re.sub(r'\s+([्ािीुूृेैोौंँ़])', r'\1', t)                     # stray space before a vowel sign / virama
    t = re.sub(r'(?<=[०-९])ण्(?=[०-९])', '.', t)                      # dates: २५ण्३ण्७६ → २५.३.७६
    if cfg.get('ddha_sha'):
        t = re.sub(r'(?<!बु)(?<!ग)ड्ढ', 'ष', t)
    if cfg.get('strip_global_no'):
        t = re.sub(r'(॥\s*[०-९]+\s*॥)\s*\(\s*[०-९]+\s*\)', r'\1', t)
    return t


# ---------------------------------------------------------------- verse marking (indented-short / tall lines with ॥N॥)
def mark_verses(lines, header_y):
    ls = sorted(lines, key=lambda l: (l[1], l[0]))
    body = [l for l in ls if l[1] > header_y]
    if not body:
        return ls
    full = [round(l[0]) for l in body if l[2] - l[0] > 200]
    base = collections.Counter(full).most_common(1)[0][0] if full else min(round(l[0]) for l in body)
    right = max(l[2] for l in body); width = max(right - base, 1)
    hs = sorted(l[3] - l[1] for l in body); med_h = hs[len(hs) // 2]
    tall = lambda l: (l[3] - l[1]) > med_h * 1.12
    marked = set()
    for i, l in enumerate(body):
        dx = l[0] - base
        if not (VNUM.search(l[4].strip()) and 8 <= dx <= 120 and ((l[2] - l[0]) < width * 0.85 or tall(l))):
            continue
        marked.add(i)
        j = i - 1
        while j >= 0 and i - j <= 6:
            p = body[j]; pdx = p[0] - base
            if not (8 <= pdx <= 120 and ((p[2] - p[0]) < width * 0.85 or tall(p))):
                break
            if VNUM.search(p[4].strip()) or re.search(r'[—\-:?]\s*$', p[4].strip()):
                break
            if re.search(r'(^|\s)(है|हैं|में|के|की|का|से|नहीं|क्या|को|यह|भी|और|तो|कि|हो|था|थे|गया)(\s|$|[।,?!])', p[4]):
                break
            marked.add(j)
            if 'उवाच' in p[4]:
                break
            j -= 1
    for i in marked:
        body[i][0] += 400
    return ls


# ---------------------------------------------------------------- section finders
def pravachan_starts(P, header_y, first=None, extra_pat=None):
    out, last = [], 0
    for i, pg in enumerate(P):
        top = sorted(pg, key=lambda l: (l[1], l[0]))[:7]
        nums = [n for n in (pnum(l[4]) for l in top) if n]
        if nums and last < nums[0] <= last + 3:
            out.append((nums[0], i + 1)); last = nums[0]
        if extra_pat:
            for l in top[:4]:
                m = re.match(extra_pat, l[4].strip())
                if m and (not out or out[-1][1] != i + 1) and not any(t == ('x', m.group(0)) for t, _ in out):
                    out.append((('x', m.group(0)), i + 1))
    if first and out and out[0][0] == 1:
        out[0] = (1, first)
    return out


def toc_entries(P, pages, offset):
    """TOC pages list 'title' then printed page number (same or next line)."""
    items = []
    for pn in pages:
        ls = [l[4].strip() for l in sorted(P[pn - 1], key=lambda l: (l[1], l[0]))]
        toks = []
        for t in ls:
            m = re.match(r'^(.*?)\s*([०-९]{1,4})$', t)
            if m and m.group(1):
                toks += [m.group(1), m.group(2)]
            else:
                toks.append(t)
        k = 0
        while k < len(toks) - 1:
            a, b = toks[k], toks[k + 1]
            if re.fullmatch(r'[०-९]{1,4}', b) and not re.fullmatch(r'[०-९]{1,4}', a) and len(a) < 60:
                items.append((a.strip(' |-'), dnum(b) + offset)); k += 2
            else:
                k += 1
    return items


# ---------------------------------------------------------------- build
def build(cfg):
    bid = cfg['id']
    P = cfg['pages']()
    N = len(P)
    GLOB = {}
    if cfg.get('global_paren'):
        for pn, pg in enumerate(P, 1):
            for l in pg:
                for m in re.finditer(r'॥\s*([०-९]+)\s*॥\s*\(\s*([०-९]+)\s*\)', l[4]):
                    GLOB[(pn, dnum(m.group(1)))] = dnum(m.group(2))
    P = [[[l[0], l[1], l[2], l[3], fix_text(l[4], cfg)] for l in pg] for pg in P]
    hy = cfg['header_y']
    pages = [mark_verses([list(l) for l in pg], hy) for pg in P]
    labels = page_labels(pages, hy, N) if not cfg.get('offset_labels') else [max(0, p - cfg['offset_labels']) for p in range(1, N + 1)]
    secs = cfg['sections'](P)
    os.makedirs(f'{OUT}/data/{bid}', exist_ok=True)
    for f in glob.glob(f'{OUT}/data/{bid}/*.json'):
        os.remove(f)
    sections, slokas = [], []
    skip = set(cfg.get('skip', []))
    for k, s in enumerate(secs):
        a = s['start']; b = secs[k + 1]['start'] - 1 if k + 1 < len(secs) else cfg['end']
        if b < a:
            continue
        bl = split_verses(parse_section(pages, a, b, s['title'], header_y=hy, para_dx=cfg.get('para_dx', (8, 60)), verse_dx=300,
                                       full_w=cfg.get('full_w', 200), skip_pages=skip, drop_start=cfg.get('drop_start')))
        if cfg.get('global_paren'):
            found = []
            for blk in bl:
                if blk['t'] == 'v' and 'n' in blk:
                    g = GLOB.get((blk['pg'], blk['n'])) or GLOB.get((blk['pg'] + 1, blk['n']))
                    if g:
                        blk['n'] = g; blk['s'] = 1; found.append(g)
                    else:
                        del blk['n']
        else:
            found = number_slokas(bl, window=12, gapfill=True) if s.get('num') else []
        rows = []
        for blk in bl:
            x, t = blk['x'], blk['t']
            if t != 'h' and len(re.findall(r'[अ-ह]', x)) < 3:
                continue
            if t == 'v' and not blk.get('s') and re.search(r'इति\s*श्री|समाप्त|सम्पूर्ण', x) and len(x) < 260:
                t = 'e'
            x = polish(t, x)
            row = [t, blk['pg'], x]
            if blk.get('s') and s.get('num'):
                row.append(blk['n'])
                slokas.append([s['num'], blk['n'], len(rows), blk['pg'], x.split('\n')[0][:80]])
            elif blk.get('c'):
                row.append(0)
            if blk.get('c'):
                row.append('c')
            rows.append(row)
        sid = s.get('id') or f's{k + 1}'
        meta = {'id': sid, 'num': s.get('num', 0), 'title': s['title'], 'group': s.get('group', 'main'), 'start': a, 'end': b}
        if s.get('sub'):
            meta['sub'] = s['sub']
        json.dump({**meta, 'blocks': rows}, open(f'{OUT}/data/{bid}/{sid}.json', 'w'), ensure_ascii=False, separators=(',', ':'))
        meta['slokas'] = len(found)
        sections.append(meta)
    first = next((s['id'] for s in sections if s['num']), sections[0]['id'])
    book = {'id': bid, 'title': cfg['title'], 'titleRoman': cfg['roman'], 'author': cfg.get('author', ''),
            'byline': cfg.get('byline', ''), 'commentator': cfg.get('commentator', COMM), 'publisher': PUB,
            'series': cfg.get('series', ''), 'pages': N, 'imgDir': f'pages/{bid}', 'labels': labels, 'firstSection': first,
            'groups': cfg.get('groups', {'front': 'प्रारम्भिक', 'main': cfg.get('sec_plural', 'प्रवचन')}),
            'secLabel': cfg.get('sec_label', 'प्रवचन'), 'secAbbr': cfg.get('sec_abbr', 'प्र.'),
            'extraPages': cfg.get('extra', [{'title': 'मुखपृष्ठ', 'page': 1}]), 'sections': sections, 'kind': cfg.get('kind', 'pravachan')}
    if cfg.get('global_paren'):
        book['globalNumbers'] = True
    json.dump(book, open(f'{OUT}/data/{bid}/book.json', 'w'), ensure_ascii=False, indent=1)
    json.dump(slokas, open(f'{OUT}/data/{bid}/slokas.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    nblocks = sum(len(json.load(open(f'{OUT}/data/{bid}/{s["id"]}.json'))['blocks']) for s in sections)
    print(f'{bid}: {len(sections)} sections, {len(slokas)} ślokas, {nblocks} blocks, pages {N}')
    return book


def drop_title(body):
    k = 0
    for i, l in enumerate(body[:6]):
        t = l[4].strip()
        if re.search(r'[।?!]', t) and len(t) > 40:
            break
        if re.search(r'ॐ|प्रवचन|नमः|^[०-९.\-\s()]+$|अनुबंध', t) or len(t) < 25:
            k = i + 1
    return body[k:]


def prav_secs(P, hy, front=None, first=None, extra=None, sub=''):
    st = pravachan_starts(P, hy, first=first, extra_pat=extra)
    secs = []
    if front:
        secs.append({'id': 'front', 'title': front[0], 'start': front[1], 'group': 'front'})
    n = 0
    for num, pg in st:
        if isinstance(num, tuple):
            secs.append({'id': f'x{len(secs)}', 'title': num[1].strip(), 'start': pg, 'group': 'appx'})
        else:
            n = num
            secs.append({'id': f'p{num}', 'num': num, 'title': f'प्रवचन {str(num).translate(D2)}', 'start': pg, 'group': 'main', 'sub': sub})
    return secs


CFG = {}
CFG['dahara'] = dict(id='dahara', title='दहरविद्या', roman='Dahara Vidyā', byline='छान्दोग्योपनिषद् (अष्टम अध्याय) की दहरविद्या पर प्रवचन',
                     pages=lambda: load_pkl('dahara'), header_y=50, end=277, ddha_sha=True, drop_start=drop_title,
                     sections=lambda P: prav_secs(P, 50, front=('प्रकाशकीय', 3)), extra=[{'title': 'मुखपृष्ठ', 'page': 1}, {'title': 'अनुक्रमणिका', 'page': 4}])
CFG['purushottama'] = dict(id='purushottama', title='श्रीपुरुषोत्तमयोग', roman='Puruṣottama Yoga', byline='श्रीमद्भगवद्गीता के पञ्चदश अध्याय पर प्रवचन',
                           pages=lambda: load_pkl('purushottama'), header_y=135, end=205, drop_start=drop_title,
                           sections=lambda P: prav_secs(P, 135, front=('प्राक्कथन', 5), first=9), extra=[{'title': 'मुखपृष्ठ', 'page': 1}, {'title': 'विषय सूची', 'page': 6}])
CFG['svetaketu'] = dict(id='svetaketu', title='श्वेतकेतुविद्या', roman='Śvetaketu Vidyā', byline='छान्दोग्योपनिषद् (षष्ठ अध्याय) पर प्रवचन',
                        pages=lambda: load_pkl('svetaketu'), header_y=45, end=299, ddha_sha=True, drop_start=drop_title,
                        sections=lambda P: prav_secs(P, 45), extra=[{'title': 'विषय-सूची', 'page': 5}])
CFG['chidananda'] = dict(id='chidananda', title='चिदानन्दलहरी', roman='Cidānanda Laharī', byline='सौन्दर्यलहरी के अष्टम श्लोक की व्याख्या (प्रवचन)',
                         pages=lambda: load_pkl('chidananda'), header_y=5, end=575, drop_start=drop_title,
                         sections=lambda P: prav_secs(P, 5, front=('प्रकाशकीय', 4), extra=r'^अनुबंध\s*[-–]?\s*[०-९]'),
                         groups={'front': 'प्रारम्भिक', 'main': 'प्रवचन', 'appx': 'अनुबन्ध'},
                         extra=[{'title': 'मुखपृष्ठ', 'page': 2}, {'title': 'क्रमसूची', 'page': 5}])


def toc_secs(P, toc_pages, offset, front=None, numbered=True, label=''):
    items = toc_entries(P, toc_pages, offset)
    secs = []
    if front:
        secs.append({'id': 'front', 'title': front[0], 'start': front[1], 'group': 'front'})
    k = 0
    for title, pg in items:
        if secs and pg <= secs[-1]['start']:
            continue
        k += 1
        secs.append({'id': f't{k}', 'num': k if numbered else 0, 'title': title, 'start': pg, 'group': 'main'})
    return secs


CFG['shivasankalpa'] = dict(id='shivasankalpa', title='शिवसंकल्पसूक्त', roman='Śiva Saṅkalpa Sūkta', byline='शुक्ल यजुर्वेद (अध्याय ३४) के शिवसंकल्पसूक्त पर प्रवचन',
                            pages=lambda: load_pkl('shivasankalpa'), header_y=62, end=552, drop_start=drop_title,
                            sections=lambda P: toc_secs(P, [3, 4], 0, front=('प्रकाशकीय', 5)),
                            sec_label='प्रकरण', sec_abbr='प्र.', groups={'front': 'प्रारम्भिक', 'main': 'प्रवचन-विषय'},
                            extra=[{'title': 'विषय-सूची', 'page': 3}])
CFG['bodhasara'] = dict(id='bodhasara', title='बोधसारः', roman='Bodhasāra', author='श्रीमदाचार्यनरहरि',
                        byline='श्रीमदाचार्यनरहरिविरचित, आचार्य दिवाकर कृत दीप्ति टीका सहित', commentator='आचार्य दिवाकर (दीप्ति टीका)',
                        pages=lambda: load_pkl('bodhasara'), header_y=70, end=830, strip_global_no=True, global_paren=True,
                        sections=lambda P: toc_secs(P, [3, 4, 5], 14, front=('प्राक्कथन', 6)), kind='granth',
                        sec_label='प्रकरण', sec_abbr='प्र.', groups={'front': 'प्रारम्भिक', 'main': 'प्रकरण'},
                        extra=[{'title': 'विषय-सूची', 'page': 3}, {'title': 'श्लोकसूची (मुद्रित)', 'page': 831}])

if __name__ == '__main__':
    for b in sys.argv[1:]:
        build(CFG[b])
