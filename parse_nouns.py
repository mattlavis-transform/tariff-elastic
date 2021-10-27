import json
from classes.wordnet import WordnetLine
import classes.globals as g

g.get_wordnet_pointer_symbols()
g.get_wordnet_lexicographer_files()
g.open_csvs()

filename = "resources/wordnet/data.noun.partial"
# filename = "resources/wordnet/data.noun"
wordnet_lines = []

synsets = []

with open(filename) as infile:
    for line in infile:
        wordnet_line = WordnetLine(line)
        if wordnet_line.valid:
            synsets.append(wordnet_line.json)
        
f = open("out.json", "w")
json.dump(synsets, f, indent=4)
f.close()
