import sys
from classes.wordnet import WordNet, WordnetLine, WordNet
import classes.globals as g

g.get_wordnet_pointer_symbols()
g.get_wordnet_lexicographer_files()
g.open_csvs()
w = WordNet()
w.clear()

filename = "resources/wordnet/data.noun.partial"
filename = "resources/wordnet/data.noun"
wordnet_lines = []

synsets = []

with open(filename) as infile:
    for line in infile:
        wordnet_line = WordnetLine(w, line)
        if wordnet_line.valid:
            synsets.append(wordnet_line.json)
