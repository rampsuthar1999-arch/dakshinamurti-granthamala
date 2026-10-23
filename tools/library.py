import json, sys, os
OUT = sys.argv[1]
META = {
    'pancadashi': {'aliases': ['पञ्चदशी', 'पंचदशी', 'पन्चदशी', 'panchadashi', 'pancadasi', 'panchadasi', 'pd'], 'mark': 'प'},
    'anubhuti': {'aliases': ['अनुभूतिप्रकाश', 'अनुभूति', 'anubhuti', 'anubhutiprakash', 'anubhooti', 'ap'], 'mark': 'अ',
                 'subtitle': 'द्वादश उपनिषदों की श्लोकबद्ध व्याख्या'},
    'krishna-sandesh': {'aliases': ['श्रीकृष्णसन्देश', 'कृष्णसन्देश', 'कृष्ण', 'गीता', 'भगवद्गीता', 'krishna', 'sandesh', 'gita', 'ks', 'bg'], 'mark': 'कृ',
                        'subtitle': 'श्रीमद्भगवद्गीता व्याख्या'},
}
ORDER = ['pancadashi', 'anubhuti', 'krishna-sandesh']
lib = []
for bid in ORDER:
    p = f'{OUT}/data/{bid}/book.json'
    if not os.path.exists(p):
        lib.append({'id': bid, 'soon': True, 'title': {'krishna-sandesh': 'श्रीकृष्ण-सन्देश', 'anubhuti': 'अनुभूतिप्रकाश'}.get(bid, bid),
                    'titleRoman': {'krishna-sandesh': 'Śrī Kṛṣṇa Sandeśa', 'anubhuti': 'Anubhūti Prakāśa'}.get(bid, ''),
                    'mark': META[bid]['mark'], 'note': 'शीघ्र उपलब्ध'})
        continue
    b = json.load(open(p))
    sl = json.load(open(f'{OUT}/data/{bid}/slokas.json'))
    lib.append({'id': bid, 'title': b['title'], 'titleRoman': b['titleRoman'], 'author': b['author'],
                'commentator': b['commentator'], 'subtitle': META[bid].get('subtitle', ''),
                'cover': f"{b['imgDir']}/{b.get('cover', 1)}.webp", 'pages': b['pages'], 'slokas': len(sl),
                'sections': len([s for s in b['sections'] if s['num']]), 'aliases': META[bid]['aliases']})
json.dump(lib, open(f'{OUT}/data/library.json', 'w'), ensure_ascii=False, indent=1)
print([(x['id'], x.get('soon', False)) for x in lib])
