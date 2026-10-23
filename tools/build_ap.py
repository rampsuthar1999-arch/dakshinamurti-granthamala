import pickle, json, os, re, sys
sys.path.insert(0, '/home/claude/work')
from structure import parse_section, split_verses, number_slokas, page_labels, polish

OUT = sys.argv[1]
BID = 'anubhuti'
P = pickle.load(open('/home/claude/work/ap/pages.pkl', 'rb'))
N = len(P)
HY = 110

CH = [  # num, title, source, start
    (1, 'ऐतरेयोपनिषद्विवरणम्', 'ऐतरेय उपनिषद्', 9),
    (2, 'तैत्तिरीयविद्याप्रकाशः', 'तैत्तिरीय उपनिषद्', 102),
    (3, 'श्वेतकेतुविद्याप्रकाशः', 'छान्दोग्य उपनिषद्', 302),
    (4, 'सनत्कुमारविद्याप्रकाशः', 'छान्दोग्य उपनिषद्', 394),
    (5, 'प्रजापतिविद्याप्रकाशः', 'छान्दोग्य उपनिषद्', 467),
    (6, 'मुण्डकविद्याप्रकाशः', 'मुण्डक उपनिषद्', 543),
    (7, 'प्रश्नोपनिषद्विवरणम्', 'प्रश्न उपनिषद्', 633),
    (8, 'इन्द्र-प्रतर्दनसंवादः', 'कौषीतकी उपनिषद्', 703),
    (9, 'बालाक्यजातशत्रुसंवादः', 'कौषीतकी उपनिषद्', 769),
    (10, 'मैत्रायण्युपनिषद्विवरणम्', 'मैत्रायणी उपनिषद्', 816),
    (11, 'कठवल्लीविवरणम्', 'कठ उपनिषद्', 903),
    (12, 'श्वेताश्वतरोपनिषद्विवरणम्', 'श्वेताश्वतर उपनिषद्', 1003),
    (13, 'कण्वविद्याप्रकाशः', 'बृहदारण्यक उपनिषद्', 1101),
    (14, 'अजातशत्रुविद्याप्रकाशः', 'बृहदारण्यक उपनिषद्', 1263),
    (15, 'मैत्रेयीविद्याप्रकाशः', 'बृहदारण्यक उपनिषद्', 1319),
    (16, 'मधुविद्याप्रकाशः', 'बृहदारण्यक उपनिषद्', 1367),
    (17, 'आश्वलायनादिमुनिबोधः', 'बृहदारण्यक उपनिषद्', 1387),
    (18, 'जनकविद्याप्रकाशः', 'बृहदारण्यक उपनिषद्', 1542),
    (19, 'तलवकारविद्याप्रकाशः', 'केन (तलवकार) उपनिषद्', 1670),
    (20, 'देवताविद्याप्रकाशः', 'नृसिंहोत्तरतापनीय उपनिषद्', 1726),
]
END = 1784
ORD = {1: 'प्रथम', 2: 'द्वितीय', 3: 'तृतीय', 4: 'चतुर्थ', 5: 'पञ्चम', 6: 'षष्ठ', 7: 'सप्तम', 8: 'अष्टम', 9: 'नवम', 10: 'दशम',
       11: 'एकादश', 12: 'द्वादश', 13: 'त्रयोदश', 14: 'चतुर्दश', 15: 'पञ्चदश', 16: 'षोडश', 17: 'सप्तदश', 18: 'अष्टादश',
       19: 'एकोनविंश', 20: 'विंश'}


def drop_start(body):
    # drop the centred title block (॥ ॐ ॥ … …ऽध्यायः … Hindi subtitle) at the top of a chapter's first page
    k = 0
    for i, l in enumerate(body[:7]):
        if re.search(r'[।|]|॥\s*[०-९]', l[4]):
            break
        if 'ध्याय' in l[4] or 'ॐ' in l[4] or 'प्रकाशः' in l[4] or 'विवरण' in l[4] or 'संवादः' in l[4] or 'बोधः' in l[4] or 'उपनिषदि' in l[4] or 'व्याख्या' in l[4]:
            k = i + 1
    return body[k:]


labels = page_labels(P, HY, N)
os.makedirs(f'{OUT}/data/{BID}', exist_ok=True)
sections, slokas = [], []
for idx, (num, title, src, a) in enumerate(CH):
    b = (CH[idx + 1][3] - 1) if idx + 1 < len(CH) else END
    bl = split_verses(parse_section(P, a, b, title, header_y=HY, para_dx=(12, 50), verse_dx=50, full_w=300, drop_start=drop_start))
    found = number_slokas(bl)
    rows = []
    for blk in bl:
        x = blk['x']
        t = blk['t']
        if t != 'h' and len(re.findall(r'[अ-ह]', x)) < 3:
            continue
        if t == 'v' and not blk.get('s') and re.search(r'^॥?\s*इति\s|समाप्त|सम्पूर्ण', x) and len(x) < 220:
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
    sid = f'a{num}'
    meta = {'id': sid, 'num': num, 'title': title, 'sub': f'{ORD[num]} अध्याय · {src}', 'group': 'g1' if num <= 7 else ('g2' if num <= 12 else 'g3'),
            'start': a, 'end': b}
    json.dump({**meta, 'blocks': rows}, open(f'{OUT}/data/{BID}/{sid}.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    meta['slokas'] = len(found)
    sections.append(meta)
    print(sid, title, 'pages', a, b, 'slokas', len(found), 'max', max(found) if found else 0,
          'gaps', sorted(set(range(1, max(found) + 1)) - set(found))[:12] if found else '')

book = {
    'id': BID, 'title': 'अनुभूतिप्रकाशः', 'titleRoman': 'Anubhūti Prakāśa',
    'author': 'श्रीमद्विद्यारण्यस्वामी', 'commentator': 'श्री १०८ स्वामी महेशानन्द गिरि जी महाराज',
    'publisher': 'श्रीदक्षिणामूर्ति मठ प्रकाशन, वाराणसी', 'series': 'द्वादश उपनिषदों की श्लोकबद्ध व्याख्या',
    'pages': N, 'imgDir': f'pages/{BID}', 'labels': labels, 'firstSection': 'a1',
    'groups': {'g1': 'भाग १ · अध्याय १–७', 'g2': 'भाग २ · अध्याय ८–१२', 'g3': 'भाग ३ · अध्याय १३–२०'},
    'secLabel': 'अध्याय', 'secAbbr': 'अ.',
    'extraPages': [{'title': 'मुखपृष्ठ एवं प्रारम्भिक पृष्ठ', 'page': 1}, {'title': 'अनुक्रमणिका (मुद्रित)', 'page': END + 1}],
    'sections': sections,
}
json.dump(book, open(f'{OUT}/data/{BID}/book.json', 'w'), ensure_ascii=False, indent=1)
json.dump(slokas, open(f'{OUT}/data/{BID}/slokas.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print('total slokas', len(slokas), 'labels sample', labels[8:12], labels[1700:1703])
