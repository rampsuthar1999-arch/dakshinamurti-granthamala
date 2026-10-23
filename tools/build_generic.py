"""Build app data for the additional books (legacy-font conversions and OCR)."""
import pickle, json, os, re, sys, collections, html, glob
sys.path.insert(0, '/home/claude/work'); sys.path.insert(0, '/home/claude/nb')
from structure import parse_section, split_verses, number_slokas, number_slokas_lis, page_labels, polish, dnum, VNUM
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


def scan_clean(t):
    t = re.sub(r'^[\s.:;,\'"`_…·\-]{2,}', '', t)          # dot-runs from shadowed margins
    t = re.sub(r'[\s.:;,\'`_…·]{3,}$', '', t)
    t = re.sub(r'\s[.:\'`_]{2,}\s', ' ', t)
    t = re.sub(r'([।॥]{1,2}\s*[०-९]{1,3}\s*[।॥]{1,2})[^।॥]{0,9}$', r'\1', t)   # junk after a verse number
    return t.strip()


def scan_normalise(lines, header_y):
    """skewed phone scans: decide paragraph starts from the previous line's length, not from indentation."""
    ls = sorted(lines, key=lambda l: (l[1], l[0]))
    body = [l for l in ls if l[1] > header_y and l[0] < 300]   # verse-marked lines were shifted by +400
    if len(body) < 3:
        return ls
    right = sorted(l[2] for l in body)[int(len(body) * 0.8)]
    base = sorted(l[0] for l in body)[len(body) // 5]
    prev_short = True
    for l in ls:
        if l[1] <= header_y:
            continue
        if l[0] >= 300:            # verse line: leave as is, next prose line starts a paragraph
            prev_short = True
            continue
        l[0] = base + 20 if prev_short else base
        prev_short = l[2] < right - 45
    return ls


def fix_text(t, cfg):
    if cfg.get('scan'):
        t = scan_clean(t)
    if cfg.get('vocab_correct'):
        sys.path.insert(0, '/home/claude/gs')
        from correct import correct_text
        t = correct_text(t)
    t = re.sub(r'\s+([्ािीुूृेैोौंँ़])', r'\1', t)                     # stray space before a vowel sign / virama
    t = re.sub(r'(?<=[०-९])ण्(?=[०-९])', '.', t)                      # dates: २५ण्३ण्७६ → २५.३.७६
    if cfg.get('ddha_sha'):
        t = re.sub(r'(?<!बु)(?<!ग)ड्ढ', 'ष', t)
    if cfg.get('strip_global_no'):
        t = re.sub(r'(॥\s*[०-९]+\s*॥)\s*\(\s*[०-९]+\s*\)', r'\1', t)
    return t


# ---------------------------------------------------------------- verse marking (indented-short / tall lines with ॥N॥)
HINDI = re.compile(r'(^|\s)(है|हैं|में|के|की|का|से|नहीं|क्या|को|यह|भी|और|तो|कि|हो|था|थे|गया|हुआ|कहते|जाता|होता|ने|पर|लिये|लिए|इस|उस|जो|वह|एक)(\s|$|[।,?!])')


def mark_verses(lines, header_y, wmax=0.85, loose=False):
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
        if not (VNUM.search(l[4].strip()) and 8 <= dx <= 120 and ((l[2] - l[0]) < width * wmax or tall(l))):
            continue
        marked.add(i)
        j = i - 1
        while j >= 0 and i - j <= 6:
            p = body[j]; pdx = p[0] - base
            if not (8 <= pdx <= 120 and ((p[2] - p[0]) < width * wmax or tall(p))):
                break
            if VNUM.search(p[4].strip()) or re.search(r'[—\-:?]\s*$', p[4].strip()):
                break
            if re.search(r'(^|\s)(है|हैं|में|के|की|का|से|नहीं|क्या|को|यह|भी|और|तो|कि|हो|था|थे|गया)(\s|$|[।,?!])', p[4]):
                break
            marked.add(j)
            if 'उवाच' in p[4]:
                break
            j -= 1
    if loose:   # skewed scans: recognise verses by content (Sanskrit lines ending in ॥N॥), not by indentation
        for i, l in enumerate(body):
            t = l[4].strip()
            if not VNUM.search(t) or (i not in marked and (HINDI.search(t) or len(t) > 90)):
                continue
            marked.add(i)
            for j in range(i - 1, max(-1, i - 4), -1):
                p = body[j][4].strip()
                if VNUM.search(p) or HINDI.search(p) or len(p) > 90 or re.search(r'[—\-:?]$', p):
                    break
                marked.add(j)
                if re.search(r'[।|]$', p) and i - j >= 1:
                    break
    for i in marked:
        body[i][0] += 400
    return ls


# ---------------------------------------------------------------- section finders
def pravachan_starts(P, header_y, first=None, extra_pat=None, kw='प्रवचन'):
    out, last = [], 0
    for i, pg in enumerate(P):
        top = sorted(pg, key=lambda l: (l[1], l[0]))[:7]
        nums = [n for n in (pnum(l[4], kw) for l in top) if n]
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
    pages = [mark_verses([list(l) for l in pg if l[4]], hy, cfg.get('verse_w', 0.85), cfg.get('loose_verse', False)) for pg in P]
    if cfg.get('scan'):
        pages = [scan_normalise(pg, hy) for pg in pages]
    labels = page_labels(pages, hy, N) if not cfg.get('offset_labels') else [max(0, p - cfg['offset_labels']) for p in range(1, N + 1)]
    if cfg.get('smooth_labels'):
        vols = cfg.get('volumes', [(1, N)])
        fixed = list(labels)
        for va, vb in vols:
            offs = sorted((i + 1) - labels[i] for i in range(va - 1, vb) if labels[i])
            if not offs:
                continue
            for i in range(va - 1, vb):
                # local offset from this volume's good labels nearby (offset drifts slowly with plates/blank pages)
                near = sorted((j + 1) - labels[j] for j in range(max(va - 1, i - 40), min(vb, i + 41))
                              if labels[j] and abs(((j + 1) - labels[j]) - offs[len(offs) // 2]) <= 8)
                med = near[len(near) // 2] if near else offs[len(offs) // 2]
                exp = (i + 1) - med
                l = labels[i]
                if l and abs(l - exp) <= 3:
                    continue
                alts = [x for x in ([l - 200, l + 200, l - 20, l + 20, l - 2, l + 2, l - 400] if l else []) if abs(x - exp) <= 3]
                fixed[i] = alts[0] if alts else exp
        labels = fixed
        for va, vb in cfg.get('volumes', []):
            for q in range(va - 1, min(vb, va - 1 + cfg.get('vol_front', 0))):
                labels[q] = 0
    secs = cfg['sections'](P, labels) if cfg.get('labels_first') else cfg['sections'](P)
    os.makedirs(f'{OUT}/data/{bid}', exist_ok=True)
    for f in glob.glob(f'{OUT}/data/{bid}/*.json'):
        os.remove(f)
    sections, slokas = [], []
    skip = set(cfg.get('skip', []))
    run_max = 0
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
        elif cfg.get('continuous'):
            found = number_slokas_lis(bl, cfg['continuous'], start_after=run_max) if s.get('num') else []
            run_max = max(found + [run_max])
        elif cfg.get('one_per_section'):
            found = []
            nxt = next((x.get('num') for x in secs[k + 1:] if x.get('num')), None)
            hi = (nxt - 1) if nxt and s.get('num') else s.get('num')
            for blk in bl:
                if blk['t'] == 'v' and s.get('num') and s['num'] <= (blk.get('n') or 0) <= hi and blk['n'] not in found:
                    blk['s'] = 1; found.append(blk['n'])
                elif blk['t'] == 'v':
                    blk.pop('n', None); blk.pop('s', None)
            if s.get('num') and not found:   # OCR damaged the number: the section opens with its verse
                for blk in bl:
                    if blk['t'] == 'v' and blk['x'].count('\n') >= 1:
                        blk['n'] = s['num']; blk['s'] = 1; found.append(s['num']); break
        elif s.get('maxn'):
            found = number_slokas_lis(bl, s['maxn'], start_after=s.get('minn', 0))
            if cfg.get('header_kw'):
                hdr = []
                for pn in range(a, b + 1):
                    for l in sorted(P[pn - 1], key=lambda l: (l[1], l[0]))[:2]:
                        m = re.search(cfg['header_kw'] + r'\s*[-–]?\s*[\'"]?\s*([०-९]{1,3})', l[4])
                        if m:
                            hdr.append((pn, dnum(m.group(1)))); break
                # LIS over header numbers (OCR noise)
                best = []
                for k, (pg, v) in enumerate(hdr):
                    bl_, bp = (1 if v <= 5 else 0), -1
                    for j in range(k):
                        if hdr[j][1] <= v <= hdr[j][1] + 4 and best[j][0] > 0 and best[j][0] + 1 > bl_:
                            bl_, bp = best[j][0] + 1, j
                    best.append((bl_, bp))
                firstpg = {}
                if best:
                    k_ = max(range(len(best)), key=lambda x: best[x][0]); seq = []
                    while k_ != -1 and best[k_][0] > 0:
                        seq.append(hdr[k_]); k_ = best[k_][1]
                    for pg, v in reversed(seq):
                        if v <= s['maxn']:
                            firstpg.setdefault(v, pg)
                have = set(found)
                for v, pg in sorted(firstpg.items()):
                    if v in have:
                        continue
                    for blk in bl:
                        if blk['t'] == 'v' and not blk.get('s') and pg - 1 <= blk['pg'] <= pg:
                            blk['n'] = v; blk['s'] = 1; found.append(v); have.add(v); break
                found = sorted(found)
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
                slokas.append([s['num'], blk['n'], len(rows), blk['pg'], x.split('\n')[0][:80], s.get('id') or f's{k + 1}'])
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
    first = cfg.get('first') or next((s['id'] for s in sections if s['num']), sections[0]['id'])
    book = {'id': bid, 'title': cfg['title'], 'titleRoman': cfg['roman'], 'author': cfg.get('author', ''),
            'byline': cfg.get('byline', ''), 'commentator': cfg.get('commentator', COMM), 'publisher': PUB,
            'series': cfg.get('series', ''), 'pages': N, 'imgDir': f'pages/{bid}', 'labels': labels, 'firstSection': first,
            'groups': cfg.get('groups', {'front': 'प्रारम्भिक', 'main': cfg.get('sec_plural', 'प्रवचन')}),
            'secLabel': cfg.get('sec_label', 'प्रवचन'), 'secAbbr': cfg.get('sec_abbr', 'प्र.'),
            'extraPages': cfg.get('extra', [{'title': 'मुखपृष्ठ', 'page': 1}]), 'sections': sections, 'kind': cfg.get('kind', 'pravachan')}
    if cfg.get('global_paren') or cfg.get('continuous') or cfg.get('one_per_section'):
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


def prav_secs(P, hy, front=None, first=None, extra=None, sub='', kw='प्रवचन', label='प्रवचन'):
    st = pravachan_starts(P, hy, first=first, extra_pat=extra, kw=kw)
    secs = []
    if front:
        secs.append({'id': 'front', 'title': front[0], 'start': front[1], 'group': 'front'})
    n = 0
    for num, pg in st:
        if isinstance(num, tuple):
            secs.append({'id': f'x{len(secs)}', 'title': num[1].strip(), 'start': pg, 'group': 'appx'})
        else:
            n = num
            secs.append({'id': f'p{num}', 'num': num, 'title': f'{label} {str(num).translate(D2)}', 'start': pg, 'group': 'main', 'sub': sub})
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



def katha_secs(P):
    toc = {}
    for pn in range(7, 13):
        for l in sorted(P[pn - 1], key=lambda l: (l[1], l[0])):
            m = re.match(r'कथा\s*[-–]\s*([०-९]{1,3})\s*[:;]\s*(.*?)\s*([०-९]{1,3})?\s*$', l[4].strip())
            if m:
                toc[dnum(m.group(1))] = (m.group(2).strip(' ।.'), dnum(m.group(3)) + 12 if m.group(3) else None)
    det = {n: pg for n, pg in pravachan_starts(P[12:], 60, kw='कथा')}
    det = {n: pg + 12 for n, pg in det.items()}
    secs = [{'id': 'front', 'title': 'प्रकाशकीय', 'start': 3, 'group': 'front'}]
    last = 12
    for n in sorted(set(toc) | set(det)):
        pg = det.get(n) or (toc.get(n, (None, None))[1])
        if not pg or pg <= last:
            continue
        t = toc.get(n, ('', None))[0]
        secs.append({'id': f'k{n}', 'num': n, 'title': f'कथा {str(n).translate(D2)}' + (f' : {t}' if t else ''), 'start': pg, 'group': 'main'})
        last = pg
    return secs


CFG['kaivalya'] = dict(id='kaivalya', title='कैवल्योपनिषद्', roman='Kaivalya Upaniṣad', byline='कैवल्योपनिषद् पर कथा-प्रवचन (व्याख्यान)',
                       pages=lambda: pickle.load(open(f'{NB}/kaivalya_ocr.pkl', 'rb')), header_y=56, end=411, drop_start=drop_title,
                       sections=katha_secs, sec_label='कथा', sec_abbr='क.', groups={'front': 'प्रारम्भिक', 'main': 'कथाएँ'},
                       extra=[{'title': 'मुखपृष्ठ', 'page': 1}, {'title': 'विषय-सूची', 'page': 7}])


NS_CH = [(1, 'प्रथमोऽध्यायः', 39, 'अज्ञान-निवृत्ति में कर्म की असमर्थता'), (2, 'द्वितीयोऽध्यायः', 142, 'महावाक्य से आत्मबोध'),
         (3, 'तृतीयोऽध्यायः', 249, 'तत्त्वमसि-वाक्यार्थ विचार'), (4, 'चतुर्थोऽध्यायः', 400, 'उपसंहार')]
CFG['naishkarmya'] = dict(id='naishkarmya', title='नैष्कर्म्यसिद्धिः', roman='Naiṣkarmya Siddhi', author='श्रीमत्सुरेश्वराचार्य',
                          byline='श्रीमत्सुरेश्वराचार्यकृत, श्रीचित्सुखाचार्यकृत भावतत्त्वप्रकाशिका सहित', commentator='श्री स्वामी प्रज्ञानानन्द सरस्वती (सानुवाद सम्पादन, श्री स्वामी महेशानन्द गिरि जी के निर्देशानुसार)',
                          pages=lambda: pickle.load(open(f'{NB}/naish_ocr.pkl', 'rb')), header_y=182, end=459, kind='granth',
                          sections=lambda P: [{'id': 'bhumika', 'title': 'भूमिका', 'start': 3, 'group': 'front'},
                                              {'id': 'prakkathan', 'title': 'प्राक्कथन', 'start': 12, 'group': 'front'}] +
                                             [{'id': f'a{n}', 'num': n, 'title': t, 'start': a, 'group': 'main', 'maxn': mx} for (n, t, a, sub), mx in zip(NS_CH, [100, 119, 126, 77])],
                          skip=list(range(17, 39)), sec_label='अध्याय', sec_abbr='अ.', groups={'front': 'प्रारम्भिक', 'main': 'अध्याय'},
                          extra=[{'title': 'मुखपृष्ठ', 'page': 1}, {'title': 'विषयानुक्रमणिका', 'page': 17}])


def heading_secs(P, pat, label, first_page=1, front=None, extra=None):
    """sections from centred title lines that match pat exactly (number in group 1)."""
    secs = [{'id': 'front', 'title': front[0], 'start': front[1], 'group': 'front'}] if front else []
    last = 0
    for i, pg in enumerate(P[first_page - 1:], first_page):
        for l in sorted(pg, key=lambda l: (l[1], l[0]))[:5]:
            m = re.match(pat, re.sub(r'\s+', ' ', l[4].strip()))
            if m:
                n = dnum(m.group(1))
                if last < n <= last + 3:
                    secs.append({'id': f'n{n}', 'num': n, 'title': f'{label} {str(n).translate(D2)}', 'start': i, 'group': 'main'})
                    last = n
                break
    for n, pg in (extra or {}).items():
        if not any(x.get('num') == n for x in secs):
            secs.append({'id': f'n{n}', 'num': n, 'title': f'{label} {str(n).translate(D2)}', 'start': pg, 'group': 'main'})
    secs.sort(key=lambda x: (x['start'], x.get('num', 0)))
    return secs


CFG['mahimna'] = dict(id='mahimna', title='श्रीशिवमहिम्नःस्तोत्रम्', roman='Śiva Mahimnaḥ Stotram', author='श्रीपुष्पदन्ताचार्य',
                      byline='श्रीपुष्पदन्ताचार्यप्रणीत, श्लोकशः व्याख्या सहित', kind='granth', one_per_section=True,
                      pages=lambda: pickle.load(open(f'{NB}/mahimna_ocr.pkl', 'rb')), header_y=60, end=233, drop_start=drop_title,
                      sections=lambda P: heading_secs(P, r'^श\S*लोक\s*[-–]\s*([०-९]{1,2})$', 'श्लोक', 7, front=('भूमिका', 3),
                                                     extra={12: 89, 13: 93, 22: 158, 31: 214, 37: 221, 40: 224}),
                      sec_label='श्लोक', sec_abbr='श्लो.', groups={'front': 'प्रारम्भिक', 'main': 'श्लोक'},
                      extra=[{'title': 'मुखपृष्ठ', 'page': 1}])


def verse_page_secs(P, a, b, maxn, label):
    """one section per verse, starting on the page where the verse (॥N॥) appears; LIS over all candidates."""
    c = []
    for pn in range(a, b + 1):
        for l in sorted(P[pn - 1], key=lambda l: (l[1], l[0])):
            m = re.search(r'[।॥]\s*([०-९]{1,3})\s*[।॥]\s*$', l[4])
            if m:
                n = dnum(m.group(1))
                for v in [n] + ([n // 10] if n > maxn else []):
                    if 1 <= v <= maxn:
                        c.append((pn, v))
    best = []
    for k, (pg, v) in enumerate(c):
        bl, bp = (1 if v <= 10 else 0), -1
        for j in range(k):
            if c[j][1] < v <= c[j][1] + 6 and best[j][0] > 0 and best[j][0] + 1 > bl:
                bl, bp = best[j][0] + 1, j
        best.append((bl, bp))
    k = max(range(len(best)), key=lambda i: best[i][0]); seq = []
    while k != -1 and best[k][0] > 0:
        seq.append(c[k]); k = best[k][1]
    first = {}
    for pg, v in reversed(seq):
        first.setdefault(v, pg)
    secs, used = [], set()
    for v in sorted(first):
        pg = first[v]
        if pg in used:
            secs[-1]['title'] = re.sub(r'(\S+)(–\S+)?$', lambda m: m.group(1) + '–' + str(v).translate(D2), secs[-1]['title'])
            continue
        used.add(pg)
        secs.append({'id': f'v{v}', 'num': v, 'title': f'{label} {str(v).translate(D2)}', 'start': pg, 'group': 'main'})
    return secs


CFG['shivananda'] = dict(id='shivananda', title='शिवानन्दलहरी', roman='Śivānanda Laharī', author='श्रीमद्भगवत्पादाचार्य (आदि शंकराचार्य)',
                         byline='श्रीमद्भगवत्पादाचार्यविरचित, हिन्दी अनुवाद तथा संस्कृत टीका सहित', kind='granth', one_per_section=True, verse_w=0.97,
                         pages=lambda: pickle.load(open(f'{NB}/shivananda_ocr.pkl', 'rb')), header_y=66, end=361, drop_start=drop_title,
                         sections=lambda P: [{'id': 'bhumika', 'title': 'भूमिका', 'start': 7, 'group': 'front'},
                                             {'id': 'avatarani', 'title': 'अवतरणिका', 'start': 29, 'group': 'front'}] +
                                            verse_page_secs(P, 35, 290, 100, 'श्लोक') +
                                            [{'id': 'tika', 'title': 'शिवानन्दलहरीव्याख्या (संस्कृत टीका)', 'start': 291, 'group': 'tika'}],
                         sec_label='श्लोक', sec_abbr='श्लो.', groups={'front': 'प्रारम्भिक', 'main': 'श्लोक एवं हिन्दी व्याख्या', 'tika': 'संस्कृत टीका'},
                         extra=[{'title': 'मुखपृष्ठ', 'page': 1}, {'title': 'विषयसूची', 'page': 3}, {'title': 'श्लोक सूची', 'page': 362}])


GS_V1 = 554
GS_SECS = [  # (title, printed page, group, num, maxn)
    ('भूमिका', None, 'front', 0, 0),
    ('भाष्य मङ्गल', 1, 'p1', 0, 0), ('सम्बन्ध ग्रन्थ', 15, 'p1', 0, 0), ('प्रथम मन्त्र', 51, 'p1', 0, 0),
    ('द्वितीय मन्त्र', 60, 'p1', 0, 0), ('तृतीय मन्त्र', 80, 'p1', 0, 0), ('चतुर्थ मन्त्र', 118, 'p1', 0, 0),
    ('पञ्चम मन्त्र', 135, 'p1', 0, 0), ('षष्ठ मन्त्र', 157, 'p1', 0, 0), ('प्रारम्भिक नौ कारिकाएँ (१–९)', 165, 'p1', 1, 9),
    ('सप्तम मन्त्र', 244, 'p1', 0, 0), ('सप्तम मन्त्र पर कारिकाएँ (१०–१८)', 301, 'p1', 1, 18), ('अष्टम मन्त्र', 399, 'p1', 0, 0),
    ('नवम मन्त्र', 410, 'p1', 0, 0), ('दशम मन्त्र', 417, 'p1', 0, 0), ('एकादश मन्त्र', 419, 'p1', 0, 0),
    ('चार मन्त्रों पर कारिकाएँ (१९–२३)', 422, 'p1', 1, 23), ('द्वादश मन्त्र', 457, 'p1', 0, 0),
    ('द्वादश मन्त्र पर कारिकाएँ (२४–२९)', 495, 'p1', 1, 29),
    ('वैतथ्य प्रकरण', ('pdf', 562), 'p2', 2, 38), ('अद्वैत प्रकरण', ('pdf', 739), 'p2', 3, 48), ('अलातशान्ति प्रकरण', ('pdf', 900), 'p2', 4, 100),
]


def gs_pages():
    return load_ocr('gs1', GS_V1) + load_ocr('gs2', 558)


def gs_secs(P, labels):
    pdf_of = {}
    for i, n in enumerate(labels, 1):
        if n and n not in pdf_of:
            pdf_of[n] = i
    out = []
    for title, pp, grp, num, mx in GS_SECS:
        if pp is None:
            pg = 4
        elif isinstance(pp, tuple):
            pg = pp[1]
        else:
            pg = pdf_of.get(pp) or next((pdf_of[q] - (q - pp) for q in range(pp, pp + 6) if q in pdf_of), None)
            if not pg:
                print('  !! no pdf page for printed', pp, title); continue
        sid = 'bh' if pp is None else f's{len(out)}'
        for q in range(GS_V1, 561):   # volume II cover and contents pages carry no printed number
            labels[q] = 0
        labels[561] = 536
        d = {'id': sid, 'num': num, 'title': title, 'start': pg, 'group': grp}
        if mx:
            d['maxn'] = mx
            d['id'] = f'pk{num}' if num > 1 else f'k1_{mx}'
            if num == 1:
                d['minn'] = {9: 0, 18: 9, 23: 18, 29: 23}[mx]
        out.append(d)
    return out


CFG['gaudapada'] = dict(id='gaudapada', title='गौडपादसार', roman='Gauḍapāda Sāra', author='',
                        byline='माण्डूक्य-उपनिषत्-कारिका व्याख्या (भाग १–२)', kind='granth',
                        pages=gs_pages, header_y=46, end=GS_V1 + 558, drop_start=drop_title, labels_first=True, scan=True, verse_w=0.9, smooth_labels=True, volumes=[(1, GS_V1), (GS_V1 + 1, GS_V1 + 558)], vol_front=0, header_kw='कारिका', skip=list(range(GS_V1 + 1, 562)), first='s1', vocab_correct=True, loose_verse=True,
                        sections=gs_secs, sec_label='प्रकरण', sec_abbr='प्र.',
                        groups={'front': 'प्रारम्भिक', 'p1': 'भाग १ · आगम प्रकरण', 'p2': 'भाग २'},
                        extra=[{'title': 'भाग १ · मुखपृष्ठ', 'page': 2}, {'title': 'भाग १ · अनुक्रमणिका', 'page': 3},
                               {'title': 'भाग २ · विषय-सूची', 'page': GS_V1 + 2}])


if __name__ == '__main__':
    for b in sys.argv[1:]:
        build(CFG[b])
