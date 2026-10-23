import json, sys, os
OUT = sys.argv[1]
# kind: granth = text + commentary (śloka-structured); pravachan = discourse collections
META = {
    'pancadashi': dict(kind='granth', aliases=['पञ्चदशी', 'पंचदशी', 'पन्चदशी', 'panchadashi', 'pancadasi', 'panchadasi', 'pd'], mark='प'),
    'anubhuti': dict(kind='granth', aliases=['अनुभूतिप्रकाश', 'अनुभूति', 'anubhuti', 'anubhutiprakash', 'anubhooti', 'ap'], mark='अ',
                     subtitle='द्वादश उपनिषदों की श्लोकबद्ध व्याख्या'),
    'krishna-sandesh': dict(kind='granth', aliases=['श्रीकृष्णसन्देश', 'कृष्णसन्देश', 'कृष्ण', 'गीता', 'भगवद्गीता', 'krishna', 'sandesh', 'gita', 'ks', 'bg'], mark='कृ'),
    'bodhasara': dict(kind='granth', aliases=['बोधसार', 'बोधसारः', 'bodhasara', 'bodhsar', 'bodhasar', 'bs'], mark='बो'),
    'naishkarmya': dict(kind='granth', aliases=['नैष्कर्म्यसिद्धि', 'नैष्कर्म्य', 'naishkarmya', 'naishkarmyasiddhi', 'ns'], mark='नै',
                        title='नैष्कर्म्यसिद्धिः', roman='Naiṣkarmya Siddhi'),
    'shivananda': dict(kind='granth', aliases=['शिवानन्दलहरी', 'शिवानंदलहरी', 'शिवानन्द', 'shivanandalahari', 'shivananda', 'sl'], mark='शि',
                       title='शिवानन्दलहरी', roman='Śivānanda Laharī'),
    'gaudapada': dict(kind='granth', aliases=['गौडपादसार', 'गौडपाद', 'माण्डूक्य', 'मांडूक्य', 'कारिका', 'gaudapada', 'gaudapadasara', 'gaudpaadsaara', 'mandukya', 'karika'], mark='गौ',
                      title='गौडपादसार', roman='Gauḍapāda Sāra'),
    'mahimna': dict(kind='granth', aliases=['शिवमहिम्नःस्तोत्र', 'महिम्न', 'महिम्नस्तोत्र', 'mahimna', 'shivamahimna', 'mahimnah'], mark='म',
                    title='श्रीशिवमहिम्नःस्तोत्रम्', roman='Śiva Mahimnaḥ Stotram'),
    'kaivalya': dict(kind='pravachan', aliases=['कैवल्योपनिषद्', 'कैवल्य', 'kaivalya', 'kaivalyopanishad'], mark='कै',
                     title='कैवल्योपनिषद्', roman='Kaivalya Upaniṣad'),
    'dahara': dict(kind='pravachan', aliases=['दहरविद्या', 'दहर', 'dahara', 'daharavidya'], mark='द'),
    'svetaketu': dict(kind='pravachan', aliases=['श्वेतकेतुविद्या', 'श्वेतकेतु', 'svetaketu', 'shvetaketu'], mark='श्वे'),
    'chidananda': dict(kind='pravachan', aliases=['चिदानन्दलहरी', 'चिदानंदलहरी', 'चिदानन्द', 'chidananda', 'chidanandalahari'], mark='चि'),
    'purushottama': dict(kind='pravachan', aliases=['पुरुषोत्तमयोग', 'पुरुषोत्तम', 'purushottama', 'purushottam'], mark='पु'),
    'shivasankalpa': dict(kind='pravachan', aliases=['शिवसंकल्पसूक्त', 'शिवसंकल्प', 'shivasankalpa', 'sivasankalpa'], mark='सं'),
}
ORDER = ['pancadashi', 'anubhuti', 'krishna-sandesh', 'gaudapada', 'bodhasara', 'naishkarmya', 'shivananda', 'mahimna',
         'kaivalya', 'dahara', 'svetaketu', 'chidananda', 'purushottama', 'shivasankalpa']
lib = []
for bid in ORDER:
    m = META[bid]
    p = f'{OUT}/data/{bid}/book.json'
    if not os.path.exists(p):
        lib.append({'id': bid, 'soon': True, 'kind': m['kind'], 'title': m.get('title', bid), 'titleRoman': m.get('roman', ''),
                    'mark': m['mark'], 'note': 'शीघ्र उपलब्ध'})
        continue
    b = json.load(open(p))
    sl = json.load(open(f'{OUT}/data/{bid}/slokas.json'))
    lib.append({'id': bid, 'kind': m['kind'], 'title': b['title'], 'titleRoman': b['titleRoman'], 'author': b.get('author', ''),
                'byline': b.get('byline', ''), 'commentator': b['commentator'], 'subtitle': m.get('subtitle', ''),
                'cover': f"{b['imgDir']}/{b.get('cover', 1)}.webp", 'pages': b['pages'], 'slokas': len(sl),
                'sections': len([s for s in b['sections'] if s['num']]), 'secLabel': b.get('secLabel', 'प्रकरण'),
                'aliases': m['aliases'], 'globalNumbers': b.get('globalNumbers', False)})
json.dump(lib, open(f'{OUT}/data/library.json', 'w'), ensure_ascii=False, indent=1)
print([(x['id'], 'soon' if x.get('soon') else x['slokas']) for x in lib])
