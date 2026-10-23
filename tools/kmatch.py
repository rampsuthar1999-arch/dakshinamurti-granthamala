"""Locate printed kārikās in OCR lines using a reference text; weighted LIS keeps them in order."""
import re, json, difflib

def norm(t):
    t = re.sub(r'[^अ-हा-ौॠ-ॣ]', '', t)   # letters + vowel signs only
    return t

def bigrams(s):
    return {s[i:i + 2] for i in range(len(s) - 1)}

def sim(a, b):
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()

def candidates(lines, ref, thr=0.62):
    """lines: list of (pos, text). ref: {n: [h1, h2]}. returns [(pos_h2, n, score, pos_h1|None)]"""
    L = [(p, norm(t), t) for p, t in lines]
    L = [(p, nt, t, bigrams(nt)) for p, nt, t in L if len(nt) >= 8]
    out = []
    for n, (h1, h2) in ref.items():
        r1, r2, rb = norm(h1), norm(h2), norm(h1 + h2)
        b1, b2, bb = bigrams(r1), bigrams(r2), bigrams(rb)
        for k, (p, nt, t, bg) in enumerate(L):
            best = None
            for which, r, b in ((2, r2, b2), (12, rb, bb)):
                if not (0.6 * len(r) <= len(nt) <= 1.5 * len(r)):
                    continue
                if len(bg & b) < 0.45 * len(b):
                    continue
                s = sim(nt, r)
                if s >= thr and (best is None or s > best[0]):
                    best = (s, which)
            if not best:
                continue
            s, which = best
            if which == 12:
                out.append((p, n, 2 * s, None)); continue
            # first half on one of the two previous lines
            s1, p1 = 0, None
            for kk in (k - 1, k - 2):
                if kk >= 0 and 0.6 * len(r1) <= len(L[kk][1]) <= 1.6 * len(r1):
                    v = sim(L[kk][1], r1)
                    if v > s1 and v >= 0.5:
                        s1, p1 = v, L[kk][0]
            out.append((p, n, s + s1, p1))
    return out

def choose(cands):
    """max-weight chain with positions and n both strictly increasing."""
    cands = sorted(cands, key=lambda c: (c[0], c[1]))
    best = []
    for i, (p, n, s, _) in enumerate(cands):
        bw, bp = s, -1
        for j in range(i):
            pj, nj, _, _ = cands[j]
            if pj < p and nj < n and best[j][0] + s > bw:
                bw, bp = best[j][0] + s, j
        best.append((bw, bp))
    if not best:
        return []
    i = max(range(len(best)), key=lambda x: best[x][0]); seq = []
    while i != -1:
        seq.append(cands[i]); i = best[i][1]
    return seq[::-1]
