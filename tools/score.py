import pickle, re, sys
sys.path.insert(0, '/home/claude/gs')
from vocab import words
V = pickle.load(open('/home/claude/gs/vocab.pkl', 'rb'))
def score(text):
    ws = [w for w in words(text) if len(w) >= 2]
    if not ws: return 0, 0
    return sum(1 for w in ws if w in V) / len(ws), len(ws)
