import os

class F:
    dir = os.path.dirname(__file__)
    cmudict = None

def load_cmudict():
    with open(os.path.join(F.dir, 'cmudict.0.7a_SPHINX_40')) as f:
        lines = f.readlines()
    F.cmudict = {}
    for line in lines:
        [word, *phonetics] = line.split()
        if word in F.cmudict:
            raise Exception(f'Duplicate word: {word}')
        F.cmudict[word] = phonetics

def convert(word):
    if not F.cmudict:
        load_cmudict()
    return F.cmudict.get(word.upper())
