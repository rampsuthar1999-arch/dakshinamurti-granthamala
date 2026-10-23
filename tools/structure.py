"""Generic page-geometry → blocks parser shared by the books.
Input: pages = list of [ [x0,y0,x1,y1,text], ... ] per pdf page (text already Unicode).
Output blocks: dicts {t: h|sh|v|tr|p|e, pg, x, n?, s?, c?}
"""
import re, collections

DEV = '०१२३४५६७८९'
VNUM = re.compile(r'[।|॥]{1,2}\s*([०-९\d]{1,3})(?:\s*[-–,]\s*[०-९\d]{1,3})?\s*[।|॥]{1,2}\s*$')
MIDNUM = re.compile(r'[।|॥]{1,2}\s*[०-९\d]{1,3}(?:\s*[-–,]\s*[०-९\d]{1,3})?\s*[।|॥]{1,2}')


def dnum(s):
    return int(''.join(str(DEV.index(c)) if c in DEV else c for c in s))


def clean(t):
    t = t.replace('।।', '॥').replace('||', '॥')
    t = re.sub(r'\s+', ' ', t).strip()
    t = re.sub(r'\s+([।॥,?!:;])', r'\1', t)
    t = t.replace('।॥', '॥')
    return t


def join_prose(lines):
    s = ''
    for x in lines:
        x = x.strip()
        if not s:
            s = x
        elif s.endswith('-') or s.endswith('—'):
            s += x
        else:
            s += ' ' + x
    return clean(s)


def merged_lines(lines):
    ls = sorted(lines, key=lambda l: (l[1], l[0]))
    out = []
    for l in ls:
        if out and abs(l[1] - out[-1][1]) < 6:
            o = out[-1]
            if l[0] < o[0]:
                o[4] = l[4] + ' ' + o[4]; o[0] = l[0]
            else:
                o[4] = o[4] + ' ' + l[4]
            o[2] = max(o[2], l[2]); o[3] = max(o[3], l[3])
        else:
            out.append(list(l))
    return out


def parse_section(pages, a, b, title, *, header_y, para_dx=(10, 40), verse_dx=40, full_w=250,
                  drop_start=None, skip_pages=()):
    """para_dx: indent range (relative to body left edge) that starts a paragraph.
    verse_dx: indent >= this means verse/centred line."""
    blocks, cur = [], None
    after_verse = False

    def flush():
        nonlocal cur
        if cur and cur['lines']:
            txt = '\n'.join(clean(x) for x in cur['lines']) if cur['t'] == 'v' else join_prose(cur['lines'])
            if txt:
                blk = {'t': cur['t'], 'pg': cur['page'], 'x': txt}
                if cur.get('cont'):
                    blk['c'] = 1
                blocks.append(blk)
        cur = None

    blocks.append({'t': 'h', 'pg': a, 'x': title})
    for pn in range(a, b + 1):
        if pn in skip_pages:
            continue
        lines = merged_lines(pages[pn - 1])
        body = [l for l in lines if l[1] >= header_y]
        if not body:
            continue
        if pn == a and drop_start:
            body = drop_start(body)
        full = [round(l[0]) for l in body if l[2] - l[0] > full_w]
        base = collections.Counter(full).most_common(1)[0][0] if full else min(round(l[0]) for l in body)
        first = True
        for l in body:
            dx, txt = l[0] - base, l[4].strip()
            if not txt:
                continue
            if dx >= verse_dx:
                if not cur or cur['t'] != 'v':
                    flush()
                    cur = {'t': 'v', 'page': pn, 'lines': []}
                if cur['lines'] and re.fullmatch(r'[।|॥]*\s*[०-९\d]{1,3}\s*[।|॥]{1,2}', txt):
                    cur['lines'][-1] += ' ' + txt
                else:
                    cur['lines'].append(txt)
                first = False
                continue
            if cur and cur['t'] == 'v':
                vtxt = clean(cur['lines'][-1]) if cur['lines'] else ''
                flush()
                after_verse = bool(VNUM.search(vtxt))
                cur = None
            new_para = para_dx[0] <= dx < para_dx[1]
            if first and not new_para and cur and cur['t'] in ('p', 'tr'):
                t = cur['t']; flush()
                cur = {'t': t, 'page': pn, 'lines': [txt], 'cont': True}
            elif new_para or not cur:
                flush()
                cur = {'t': 'tr' if after_verse else 'p', 'page': pn, 'lines': [txt]}
                after_verse = False
            else:
                cur['lines'].append(txt)
            first = False
    flush()
    return blocks


def split_verses(blocks):
    """split verse blocks at internal verse numbers; peel short sub-headings off the top."""
    out = []
    for b in blocks:
        if b['t'] != 'v':
            out.append(b); continue
        lines = b['x'].split('\n')
        # leading short lines without dandas = centred sub-headings (e.g. प्रतिज्ञा)
        while len(lines) > 1 and len(lines[0]) <= 32 and not re.search(r'[।॥|]', lines[0]):
            out.append({'t': 'sh', 'pg': b['pg'], 'x': lines.pop(0)})
        if len(lines) == 1 and len(lines[0]) <= 32 and not re.search(r'[।॥|]', lines[0]):
            out.append({'t': 'sh', 'pg': b['pg'], 'x': lines[0]}); continue
        cur = []
        for ln in lines:
            m = MIDNUM.search(ln)
            if m and m.end() < len(ln) - 3:
                cur.append(ln[:m.end()]); out.append({'t': 'v', 'pg': b['pg'], 'x': '\n'.join(cur)})
                cur = [ln[m.end():].strip()]
            elif m:
                cur.append(ln); out.append({'t': 'v', 'pg': b['pg'], 'x': '\n'.join(cur)}); cur = []
            else:
                cur.append(ln)
        if cur:
            out.append({'t': 'v', 'pg': b['pg'], 'x': '\n'.join(cur)})
    for b in out:
        if b['t'] == 'v':
            m = VNUM.search(b['x'])
            if m:
                b['n'] = dnum(m.group(1))
    # a paragraph right after a numbered verse is its meaning
    for i in range(1, len(out)):
        if out[i]['t'] == 'tr' and not (out[i - 1]['t'] == 'v' and 'n' in out[i - 1]):
            out[i]['t'] = 'p'
    return out


def number_slokas(blocks, window=8, gapfill=False):
    """mark the main śloka sequence (numbers increasing from 1)."""
    expected, found = 1, []
    for b in blocks:
        if b['t'] != 'v' or 'n' not in b:
            continue
        if expected <= b['n'] <= expected + window:
            b['s'] = 1; found.append(b['n']); expected = b['n'] + 1
        else:
            del b['n']
    if gapfill:
        main = [i for i, b in enumerate(blocks) if b.get('s')]
        bounds = [(-1, 0)] + [(i, blocks[i]['n']) for i in main]
        for (a_, na), (b_, nb) in zip(bounds, bounds[1:]):
            gap = nb - na - 1
            if gap <= 0:
                continue
            cand = [i for i in range(a_ + 1, b_) if blocks[i]['t'] == 'v' and 'n' not in blocks[i] and blocks[i]['x'].count('\n') >= 1]
            if len(cand) == gap:
                for k, i in enumerate(cand):
                    blocks[i]['n'] = na + 1 + k; blocks[i]['s'] = 1; found.append(na + 1 + k)
    return sorted(found)


def page_labels(pages, header_y, npages):
    """printed page number per pdf page (from header digits), gaps filled by neighbours."""
    lab = [None] * (npages + 1)
    for i in range(1, npages + 1):
        top = [l for l in pages[i - 1] if l[1] < header_y]
        for l in top:
            m = re.fullmatch(r'\s*([०-९]{1,4})\s*', l[4])
            if m:
                lab[i] = dnum(m.group(1)); break
            m = re.match(r'^([०-९]{1,4})\s', l[4]) or re.search(r'\s([०-९]{1,4})$', l[4])
            if m and not re.match(r'^[०-९]+[-–]', l[4]):
                lab[i] = dnum(m.group(1)); break
    # keep only labels consistent with a neighbour (+-1 page)
    good = [None] * (npages + 1)
    for i in range(1, npages + 1):
        if lab[i] is None:
            continue
        ok = any(0 < j <= npages and lab[j] is not None and lab[j] - lab[i] == j - i for j in (i - 2, i - 1, i + 1, i + 2))
        if ok:
            good[i] = lab[i]
    # fill gaps from previous good label
    out = [0] * (npages + 1)
    last_i, last_v = None, None
    for i in range(1, npages + 1):
        if good[i] is not None:
            last_i, last_v = i, good[i]; out[i] = good[i]
        elif last_i is not None:
            out[i] = last_v + (i - last_i)
    # back-fill pages before the next good label (chapter openings have no header)
    nxt_i = None
    for i in range(npages, 0, -1):
        if good[i] is not None:
            nxt_i = i
        elif nxt_i is not None and (out[i] == 0 or (i < nxt_i and out[i] != good[nxt_i] - (nxt_i - i))):
            v = good[nxt_i] - (nxt_i - i)
            if v > 0 and (out[i] == 0 or nxt_i - i <= 2):
                out[i] = v
    return out[1:]


def polish(t, x):
    """final text clean-ups shared by all books."""
    x = re.sub(r"([’'”\"])्", r"्\1", x)
    x = re.sub(r'[\x00-\x09\x0b-\x1f\x7f-\x9f]', '', x)
    if t == 'v':
        lines = x.split('\n')
        out = []
        for ln in lines:
            if out and re.fullmatch(r'[\s॥।|०-९\d\-–/]+', ln):
                out[-1] = out[-1].rstrip() + ' ' + ln.strip()
            else:
                out.append(ln)
        x = '\n'.join(out)
        x = re.sub(r'[।॥|]{1,2}\s*([०-९]{1,3})\s*[।॥|]{1,2}\s*$', r'॥ \1॥', x)
    x = x.replace('।।', '॥')
    return x


def number_slokas_lis(blocks, maxn, max_step=15, start_after=0):
    """Choose verse numbers as the longest strictly increasing sequence (robust to stray/false numbers).
    OCR noise: a number > maxn is also tried with its last digit dropped (२९२ → २९)."""
    cands = []  # (block index, value)
    for i, b in enumerate(blocks):
        if b['t'] != 'v' or 'n' not in b:
            continue
        vals = [b['n']]
        if b['n'] > maxn and b['n'] >= 10:
            vals.append(b['n'] // 10)
        for v in vals:
            if start_after < v <= maxn:
                cands.append((i, v))
    # LIS over (index order, value strictly increasing, step <= max_step), one value per block
    best = []  # best[k] = (length, prev_k)
    for k, (i, v) in enumerate(cands):
        bl, bp = 1 if v <= start_after + max_step else 0, -1
        for j in range(k):
            ij, vj = cands[j]
            if ij < i and vj < v <= vj + max_step and best[j][0] > 0 and best[j][0] + 1 > bl:
                bl, bp = best[j][0] + 1, j
        best.append((bl, bp))
    if not best:
        return []
    k = max(range(len(best)), key=lambda x: best[x][0])
    chosen = {}
    while k != -1 and best[k][0] > 0:
        i, v = cands[k]; chosen[i] = v; k = best[k][1]
    for i, b in enumerate(blocks):
        if b['t'] == 'v':
            if i in chosen:
                b['n'] = chosen[i]; b['s'] = 1
            else:
                b.pop('n', None); b.pop('s', None)
    # gap fill: unnumbered 2+-line verse blocks exactly filling a gap
    main = sorted(chosen)
    bounds = [(-1, start_after)] + [(i, chosen[i]) for i in main]
    for (a_, na), (b_, nb) in zip(bounds, bounds[1:]):
        gap = nb - na - 1
        if gap <= 0:
            continue
        cand = [i for i in range(a_ + 1, b_) if blocks[i]['t'] == 'v' and 's' not in blocks[i] and blocks[i]['x'].count('\n') >= 1]
        if len(cand) == gap:
            for kk, i in enumerate(cand):
                blocks[i]['n'] = na + 1 + kk; blocks[i]['s'] = 1; chosen[i] = na + 1 + kk
    return sorted(chosen.values())
