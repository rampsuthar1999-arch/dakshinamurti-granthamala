import re, html
DEV='०१२३४५६७८९'
def dnum(s):
    return int(''.join(str(DEV.index(c)) if c in DEV else c for c in s))
def load_pages(path='bbox.html'):
    src=open(path).read()
    pages=[]
    for pg in src.split('<page ')[1:]:
        ls=[]
        for m in re.finditer(r'<line xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</line>',pg,re.S):
            ws=[html.unescape(w) for w in re.findall(r'<word[^>]*>(.*?)</word>',m.group(5))]
            ls.append([float(m.group(1)),float(m.group(2)),float(m.group(3)),float(m.group(4)),' '.join(ws)])
        pages.append(ls)
    return pages
