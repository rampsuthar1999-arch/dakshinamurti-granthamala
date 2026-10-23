import json, glob, re, collections, pickle, sys
W = re.compile(r'[ऀ-ॣ॰-ॿ‌‍]+')
def words(t):
    return [w.replace('‌', '').replace('‍', '') for w in W.findall(t)]
if __name__ == '__main__':
    c = collections.Counter()
    for b in ['anubhuti', 'krishna-sandesh', 'bodhasara', 'dahara', 'purushottama', 'svetaketu', 'chidananda', 'shivasankalpa']:
        for f in glob.glob(f'/home/claude/dakshinamurti-granthamala/data/{b}/*.json'):
            if f.endswith(('book.json', 'slokas.json')): continue
            if b == 'krishna-sandesh' and re.search(r'/(g[13-9]|bhumika|dhyana)\.json$', f): continue   # OCR chapters
            for blk in json.load(open(f))['blocks']:
                c.update(w for w in words(blk[2]) if len(w) >= 2)
    pickle.dump(c, open('vocab.pkl', 'wb'))
    print(len(c), 'distinct words,', sum(c.values()), 'tokens')
