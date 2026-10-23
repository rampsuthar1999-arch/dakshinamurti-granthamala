import pickle, json, os, re, sys
sys.path.insert(0, '/home/claude/work')
OUT = sys.argv[1]
os.makedirs(f'{OUT}/data/pancadashi', exist_ok=True)
allsec = pickle.load(open('/home/claude/work/parsed.pkl', 'rb'))

FIX = [('पज्चदशी', 'पञ्चदशी'), ('पजञ्चदशी', 'पञ्चदशी'), ('‍', '')]


def fix(t):
    for a, b in FIX:
        t = t.replace(a, b)
    return t


sections = []
slokas = []
for (sid, num, title, group, a, b), blocks in allsec:
    rows = []
    for i, bl in enumerate(blocks):
        t = bl['t']
        x = fix(bl['x'])
        if len(re.findall(r'[\u0905-\u0939]', x)) < 4 and t != 'h':
            continue
        if t == 'v' and not bl.get('s') and re.search(r'समाप्त|सम्पूर्ण|पूर्ण हुआ', x) and len(x) < 160:
            t = 'e'
        row = [t, bl['pg'], x]
        if bl.get('s'):
            row.append(bl['n'])
            slokas.append([num, bl['n'], len(rows), bl['pg'], x.split('\n')[0][:80]])
        elif bl.get('c'):
            row.append(0)
        if bl.get('c'):
            row.append('c')
        rows.append(row)
    sec = {'id': sid, 'num': num, 'title': title, 'group': group, 'start': a, 'end': b}
    json.dump({**sec, 'blocks': rows}, open(f'{OUT}/data/pancadashi/{sid}.json', 'w'),
              ensure_ascii=False, separators=(',', ':'))
    sec['slokas'] = sum(1 for r in rows if len(r) > 3 and r[0] == 'v' and r[3])
    sections.append(sec)

book = {
    'id': 'pancadashi',
    'title': 'पञ्चदशी',
    'titleRoman': 'Pañcadaśī',
    'author': 'श्रीमद्विद्यारण्यस्वामी',
    'commentator': 'श्री १०८ स्वामी महेशानन्द गिरि जी महाराज',
    'publisher': 'श्रीदक्षिणामूर्ति मठ प्रकाशन, वाराणसी',
    'series': 'श्रीदक्षिणामूर्तिसंस्कृतग्रन्थमाला – ८२',
    'pages': 1530,
    'pageOffset': 10,  # printed page = pdf page - 10 (for pdf page >= 11)
    'imgDir': 'pages/pancadashi',
    'groups': {
        'front': 'प्रारम्भिक',
        'viveka': 'पञ्च विवेक',
        'dipa': 'पञ्च दीप',
        'ananda': 'पञ्च आनन्द (ब्रह्मानन्द)',
    },
    'extraPages': [
        {'title': 'मुखपृष्ठ', 'page': 1},
        {'title': 'विषय सूची', 'page': 10},
        {'title': 'श्लोकसूची (मुद्रित)', 'page': 1507},
    ],
    'sections': sections,
}
json.dump(book, open(f'{OUT}/data/pancadashi/book.json', 'w'), ensure_ascii=False, indent=1)
json.dump(slokas, open(f'{OUT}/data/pancadashi/slokas.json', 'w'), ensure_ascii=False, separators=(',', ':'))
json.dump([{'id': 'pancadashi', 'title': book['title'], 'titleRoman': book['titleRoman'],
            'author': book['author'], 'commentator': book['commentator'], 'cover': 'pages/pancadashi/1.webp',
            'pages': 1530, 'slokas': len(slokas)}],
          open(f'{OUT}/data/library.json', 'w'), ensure_ascii=False, indent=1)
print('slokas', len(slokas))
