import sys
from nltk.corpus import wordnet

synonyms = []
antonyms = []

term = sys.argv[1]

syns = wordnet.synsets(term)

for syn in syns:
    part_of_speech = syn.pos()
    if part_of_speech == "n":
        print (syn.name(), ":", syn.definition(), ":", syn.pos())
        print (syn.part_holonyms())

sys.exit()
for syn in wordnet.synsets(term):
    for l in syn.lemmas():
        synonyms.append(l.name())
        if l.antonyms():
            antonyms.append(l.antonyms()[0].name())

# print(set(synonyms))
# print(set(antonyms))