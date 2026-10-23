import pickle, re, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from parse_common import dnum

P = pickle.load(open('pages.pkl', 'rb'))
DEV = '०१२३४५६७८९'

SECTIONS = [
    # id, num, title, group, start, end (pdf pages, inclusive)
    ('bhumika', 0, 'भूमिका', 'front', 4, 8),
    ('p1', 1, 'तत्त्वविवेक प्रकरण', 'viveka', 11, 148),
    ('p2', 2, 'महाभूतविवेक प्रकरण', 'viveka', 149, 262),
    ('p3', 3, 'पञ्चकोशविवेक प्रकरण', 'viveka', 263, 328),
    ('p4', 4, 'द्वैतविवेक प्रकरण', 'viveka', 329, 408),
    ('p5', 5, 'महावाक्यविवेक प्रकरण', 'viveka', 409, 416),
    ('p6', 6, 'चित्रदीप प्रकरण', 'dipa', 417, 684),
    ('p7', 7, 'तृप्तिदीप प्रकरण', 'dipa', 685, 946),
    ('p8', 8, 'कूटस्थदीप प्रकरण', 'dipa', 947, 1010),
    ('p9', 9, 'ध्यानदीप प्रकरण', 'dipa', 1011, 1160),
    ('p10', 10, 'नाटकदीप प्रकरण', 'dipa', 1161, 1186),
    ('p11', 11, 'ब्रह्मानन्द में योगानन्द प्रकरण', 'ananda', 1187, 1298),
    ('p12', 12, 'ब्रह्मानन्द में आत्मानन्द प्रकरण', 'ananda', 1299, 1380),
    ('p13', 13, 'ब्रह्मानन्द में अद्वैतानन्द प्रकरण', 'ananda', 1381, 1446),
    ('p14', 14, 'ब्रह्मानन्द में विद्यानन्द प्रकरण', 'ananda', 1447, 1484),
    ('p15', 15, 'ब्रह्मानन्द में विषयानन्द प्रकरण', 'ananda', 1485, 1506),
]
EXPECTED = {1: 65, 2: 109, 3: 43, 4: 69, 5: 8, 6: 290, 7: 298, 8: 76, 9: 158, 10: 26,
            11: 134, 12: 90, 13: 105, 14: 65, 15: 35}

VNUM = re.compile(r'[।|॥]{1,2}\s*([०-९\d]{1,3})\s*[।|॥]{1,2}\s*$')


def merged_lines(pn):
    ls = sorted(P[pn - 1], key=lambda l: (l[1], l[0]))
    out = []
    for l in ls:
        if out and abs(l[1] - out[-1][1]) < 6:
            o = out[-1]
            if l[0] < o[0]:
                o[4] = l[4] + ' ' + o[4]
                o[0] = l[0]
            else:
                o[4] = o[4] + ' ' + l[4]
            o[2] = max(o[2], l[2]); o[3] = max(o[3], l[3])
        else:
            out.append(list(l))
    return out


def clean(t):
    t = t.replace('।।', '॥').replace('||', '॥')
    t = re.sub(r'\s+', ' ', t).strip()
    t = re.sub(r'\s+([।॥,?!:;])', r'\1', t)
    t = t.replace('॥ ', '॥ ').replace('।॥', '॥')
    return t


def join_prose(lines):
    s = ''
    for x in lines:
        x = x.strip()
        if not s:
            s = x
        elif s.endswith('-'):
            s += x
        else:
            s += ' ' + x
    return clean(s)


def parse_section(sec):
    sid, num, title, group, a, b = sec
    blocks = []  # dicts
    cur = None   # current prose para being built: {'t':type,'page':p,'lines':[]}

    def flush():
        nonlocal cur
        if cur and cur['lines']:
            if cur['t'] == 'v':
                txt = '\n'.join(clean(x) for x in cur['lines'])
            else:
                txt = join_prose(cur['lines'])
            if txt:
                blk = {'t': cur['t'], 'pg': cur['page'], 'x': txt}
                if cur.get('cont'):
                    blk['c'] = 1
                blocks.append(blk)
        cur = None

    after_verse = False
    for pn in range(a, b + 1):
        lines = merged_lines(pn)
        body = [l for l in lines if l[1] >= 52]
        if pn == a and num >= 1:
            # drop ordinal + title lines at top of prakarana start page
            k = 0
            for i, l in enumerate(body[:4]):
                if 'प्रकरण' in l[4] or len(l[4]) < 12:
                    k = i + 1
                    if 'प्रकरण' in l[4]:
                        break
            body = body[k:]
            blocks.append({'t': 'h', 'pg': pn, 'x': title})
        if sid == 'bhumika' and pn == a:
            body = [l for l in body if l[4].strip() != 'भूमिका']
            blocks.append({'t': 'h', 'pg': pn, 'x': 'भूमिका'})
        first = True
        import collections
        full = [round(l[0]) for l in body if l[2] - l[0] > 250]
        base = collections.Counter(full).most_common(1)[0][0] if full else 36
        if base > 60 or base < 20: base = 36
        for l in body:
            x0, txt = l[0] - base + 36, l[4].strip()
            if not txt:
                continue
            is_v = x0 >= 64
            if is_v:
                if not cur or cur['t'] != 'v':
                    flush()
                    cur = {'t': 'v', 'page': pn, 'lines': []}
                # verse number on separate short line -> append to previous line
                if cur['lines'] and re.fullmatch(r'[।|]*\s*[०-९\d]{1,3}\s*[।|]{1,2}', txt):
                    cur['lines'][-1] += ' ' + txt
                else:
                    cur['lines'].append(txt)
                first = False
                continue
            # prose line
            if cur and cur['t'] == 'v':
                vtxt = cur['lines'][-1] if cur['lines'] else ''
                flush()
                after_verse = bool(VNUM.search(clean(vtxt)))
                if after_verse:
                    blocks[-1]['n'] = dnum(VNUM.search(clean(vtxt)).group(1))
                cur = None
            new_para = 46 <= x0 < 64
            if first and not new_para and cur and cur['t'] in ('p', 'tr'):
                # continuation of a paragraph from previous page
                t = cur['t']
                flush()
                cur = {'t': t, 'page': pn, 'lines': [txt], 'cont': True}
            elif new_para or not cur:
                flush()
                t = 'tr' if after_verse else 'p'
                after_verse = False
                cur = {'t': t, 'page': pn, 'lines': [txt]}
                if not new_para and blocks and blocks[-1]['t'] == 'h' and False:
                    pass
            else:
                cur['lines'].append(txt)
            first = False
        # carry over to next page: keep cur open
    if cur and cur['t'] == 'v':
        vtxt = cur['lines'][-1]
        flush()
        m = VNUM.search(clean(vtxt))
        if m:
            blocks[-1]['n'] = dnum(m.group(1))
    flush()
    return blocks


MIDNUM = re.compile(r'[।|॥]{1,2}\s*[०-९\d]{1,3}\s*[।|॥]{1,2}')


def split_verses(blocks):
    out = []
    for b in blocks:
        if b['t'] != 'v':
            out.append(b); continue
        lines = b['x'].split('\n')
        cur = []
        for ln in lines:
            # a line may itself contain a number mid-line (verse end + next start)
            m = MIDNUM.search(ln)
            if m and m.end() < len(ln) - 3:
                cur.append(ln[:m.end()])
                out.append({'t': 'v', 'pg': b['pg'], 'x': '\n'.join(cur)})
                cur = [ln[m.end():].strip()]
            elif m:
                cur.append(ln)
                out.append({'t': 'v', 'pg': b['pg'], 'x': '\n'.join(cur)})
                cur = []
            else:
                cur.append(ln)
        if cur:
            out.append({'t': 'v', 'pg': b['pg'], 'x': '\n'.join(cur)})
        # keep number on last-ending fragment
    for b in out:
        if b['t'] == 'v' and 'n' not in b:
            m = VNUM.search(b['x'])
            if m:
                b['n'] = dnum(m.group(1))
    return out


def assign_verse_numbers(blocks, num):
    """Pick the main sloka sequence: numbered verse blocks whose numbers increase.
    Fix OCR digit confusion (९<->१) using expected sequence."""
    if num < 1:
        return []
    expected = 1
    found = []
    for b in blocks:
        if b['t'] != 'v' or 'n' not in b:
            continue
        n = b['n']
        cands = {n}
        s = str(n)
        # OCR confuses ९ with १ and ६, and drops/adds digits
        import itertools
        CONF = {'1': '19', '9': '916', '6': '69'}
        opts = [CONF.get(ch, ch) for ch in s]
        for combo in itertools.product(*opts):
            cands.add(int(''.join(combo)))
        best = None
        for c in sorted(cands, key=lambda c: (abs(c - expected), c != n)):
            if expected <= c <= expected + 6:
                best = c; break
        if best is None:
            # verse quoted from elsewhere, or out of order: mark as quote
            del b['n']
            continue
        b['n'] = best
        b['s'] = 1  # main sloka
        found.append(best)
        expected = best + 1
    # gap fill: unnumbered 2+-line verse blocks between consecutive found slokas
    main = [i for i, b in enumerate(blocks) if b.get('s')]
    for a_, b_ in zip(main, main[1:]):
        gap = blocks[b_]['n'] - blocks[a_]['n'] - 1
        if gap <= 0:
            continue
        cand = [i for i in range(a_ + 1, b_) if blocks[i]['t'] == 'v' and 'n' not in blocks[i]
                and blocks[i]['x'].count('\n') >= 1]
        if len(cand) == gap:
            for k, i in enumerate(cand):
                blocks[i]['n'] = blocks[a_]['n'] + 1 + k
                blocks[i]['s'] = 1
                blocks[i]['g'] = 1  # number inferred
                found.append(blocks[i]['n'])
    return found


if __name__ == '__main__':
    os.makedirs('data', exist_ok=True)
    allsec = []
    total = 0
    for sec in SECTIONS:
        bl = split_verses(parse_section(sec))
        found = assign_verse_numbers(bl, sec[1])
        if sec[1] >= 1:
            exp = EXPECTED[sec[1]]
            missing = sorted(set(range(1, exp + 1)) - set(found))
            print(f'{sec[0]}: blocks={len(bl)} slokas found {len(set(found))}/{exp} missing={missing[:30]}{"..." if len(missing)>30 else ""}')
            total += len(set(found))
        allsec.append((sec, bl))
    print('total slokas', total)
    pickle.dump(allsec, open('parsed.pkl', 'wb'))
