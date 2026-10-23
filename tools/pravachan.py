import pickle, sys, re
sys.path.insert(0, '/home/claude/work')
from structure import dnum
ORDW = {'प्रथम': 1, 'पहला': 1, 'द्वितीय': 2, 'दूसरा': 2, 'तृतीय': 3, 'तीसरा': 3, 'चतुर्थ': 4, 'चौथा': 4, 'चैथा': 4, 'पंचम': 5, 'पञ्चम': 5, 'पाँचवाँ': 5,
        'षष्ठ': 6, 'छठा': 6, 'सप्तम': 7, 'सातवाँ': 7, 'अष्टम': 8, 'आठवाँ': 8, 'नवम': 9, 'नौवाँ': 9, 'दशम': 10, 'दसवाँ': 10, 'एकादश': 11,
        'द्वादश': 12, 'त्रयोदश': 13, 'चतुर्दश': 14, 'चर्तुदश': 14, 'पंचदश': 15, 'प॰चदश': 15, 'पञ्चदश': 15, 'षोडश': 16, 'सप्तदश': 17, 'अष्टादश': 18,
        'एकोनविंश': 19, 'विंश': 20}


def pnum(t):
    t = re.sub(r'\s+([्ािीुूृेैोौंँ])', r'\1', t.strip())
    if len(t) > 30 or 'प्रवचन' not in t:
        return None
    m = re.search(r'प्रवचन\s*[-–:]?\s*([०-९]{1,2})', t)
    if m:
        return dnum(m.group(1))
    for w, n in sorted(ORDW.items(), key=lambda x: -len(x[0])):
        if t.startswith(w):
            return n
    return None


def transitions(P):
    out, last = [], 0
    for i, pg in enumerate(P):
        nums = [pnum(l[4]) for l in sorted(pg, key=lambda l: (l[1], l[0]))[:6]]
        nums = [n for n in nums if n]
        if nums and nums[0] != last and nums[0] == last + 1:
            out.append((nums[0], i + 1)); last = nums[0]
    return out


if __name__ == '__main__':
    for b in sys.argv[1:]:
        P = pickle.load(open(f'{b}.pkl', 'rb'))
        print(b, transitions(P))
