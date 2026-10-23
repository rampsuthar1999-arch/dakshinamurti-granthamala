"""Vocabulary-checked OCR correction for scanned books.
A word is changed only if it is NOT in the reference vocabulary and a candidate built from known
OCR confusions IS in it (frequency >= MINF). Reference = font-converted books (accurate text)."""
import pickle, re, itertools, functools, sys
sys.path.insert(0, '/home/claude/gs')
V = pickle.load(open('/home/claude/gs/vocab.pkl', 'rb'))
MINF = 3
# extra reference texts (e.g. the standard Māṇḍūkya-kārikā text): their words count as well attested
import json as _json, os as _os
for _p in ['/home/claude/ref/kref.json']:
    if _os.path.exists(_p):
        for _v in _json.load(open(_p)).values():
            for _w in re.findall(r'[\u0900-\u0963\u0970-\u097F]+', ' '.join(_v)):
                V[_w] = V.get(_w, 0) + MINF

# (wrong, right) substring confusions observed in this OCR
SUBS = [('ट्रैत', 'द्वैत'), ('ट्वैत', 'द्वैत'), ('द्रैत', 'द्वैत'), ('दट्वैत', 'द्वैत'), ('ट्रै', 'द्वै'), ('द्रय', 'द्वय'),
        ('ख्र', 'स्त्र'), ('शास्र', 'शास्त्र'), ('य्र', 'ग्र'), ('त्र', 'न्न'), ('न्र', 'न्न'), ('ह्म', 'ह्य'), ('त्त', 'त्र'),
        ('स्वप्त', 'स्वप्न'), ('स्वन', 'स्वप्न'), ('स्वण', 'स्वप्न'), ('बाहा', 'बाह्य'), ('ड्ड', 'ड्ढ'), ('फ्ति', 'प्ति'),
        ('प्ज्ञ', 'प्रज्ञ'), ('त्रह्म', 'ब्रह्म'), ('ख्रह्म', 'रब्रह्म'), ('ब्रह्र', 'ब्रह्म'), ('शेय', 'ज्ञेय'), ('अहण', 'ग्रहण'),
        ('तत्ति', 'त्पत्ति'), ('ध्या', 'थ्या'), ('ध्य', 'थ्य'), ('घ', 'ध'), ('ध', 'घ'), ('प', 'ष'), ('ष', 'प'), ('व', 'ब'), ('ब', 'व'),
        ('म', 'भ'), ('भ', 'म'), ('ढ', 'ड'), ('ड', 'ढ'), ('ज्', 'ज्ञ'), ('ज्ञ', 'ज्'), ('द्ध', 'द्व'), ('द्व', 'द्ध'),
        ('ट', 'ठ'), ('ञ', 'ज्ञ'), ('ख', 'रव'), ('रव', 'ख'), ('ऑ', 'ओ'), ('ञ्', 'ङ्'), ('ड़', 'ड'), ('ड', 'ड़')]
VOW = [('े', 'ै'), ('ै', 'े'), ('ो', 'ौ'), ('ौ', 'ो'), ('ि', 'ी'), ('ी', 'ि'), ('ु', 'ू'), ('ू', 'ु')]
MARKS = 'ंँ॒॑'


def _edits(w):
    out = set()
    # drop stray nasal / accent marks (one at a time, then all)
    for i, ch in enumerate(w):
        if ch in MARKS:
            out.add(w[:i] + w[i + 1:])
    out.add(''.join(ch for ch in w if ch not in '॒॑'))
    out.add(''.join(ch for ch in w if ch not in MARKS))
    # word-final तू/दू → त्/द् (halant read as ू)
    out.add(re.sub(r'([तदनमक])ू$', r'\1्', w))
    for a, b in SUBS + VOW:
        start = 0
        while True:
            i = w.find(a, start)
            if i < 0:
                break
            out.add(w[:i] + b + w[i + len(a):])
            start = i + 1
    out.discard(w)
    return out


@functools.lru_cache(maxsize=None)
def fix_word(w):
    if len(w) < 2 or w in V:
        return w
    if len(w) == 2 and w[1] in 'ंँ' and w[0] in ONE:
        return w[0]
    best, bf = None, 0
    c1 = _edits(w)
    for c in c1:
        f = V.get(c, 0)
        if f > bf:
            best, bf = c, f
    if not best and len(w) >= 4:          # two edits (e.g. stray anusvara + confusion)
        for c in c1:
            for c2 in _edits(c):
                f = V.get(c2, 0)
                if f > bf:
                    best, bf = c2, f
    return best if best and bf >= MINF else w


JUNK = re.compile(r'(?<![\u0900-\u0963\u0970-\u097F])(?:[घाएहकंॅड़ेँ]{1,5}|[लअआ][्ं])(?![\u0900-\u0963\u0970-\u097F])')
ONE = {'न', 'व', 'ॐ', 'स', 'अ'}
WORD = re.compile(r'[ऀ-ॣ॰-ॿ]+')


def correct_text(t):
    t = t.replace('॑', '').replace('॒', '')
    t = WORD.sub(lambda m: fix_word(m.group(0)), t)
    # margin junk left by shadows (only tokens that are not real words)
    t = JUNK.sub(lambda m: m.group(0) if m.group(0) in V else '', t)
    return re.sub(r'\s{2,}', ' ', t).strip()


if __name__ == '__main__':
    for w in ['ट्रैत', 'शाख्र', 'जाय्रतू', 'यहं', 'गयां', 'स्वप्त', 'भित्र', 'परत्रह्म', 'सुषुफ्ति', 'मिध्या', 'जेसे', 'बेठे', 'अद्रैत', 'नागार्जुन', 'आत्मसत्यानुबोध']:
        print(w, '→', fix_word(w))
