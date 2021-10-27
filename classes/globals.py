import csv
import os
from dotenv import load_dotenv

filters = {}

def get_wordnet_pointer_symbols():
    global pointer_symbols
    pointer_symbols = {}
    with open('resources/wordnet/pointer_symbols.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            if len(row) > 2:
                pointer_symbols[row[0]] = row[1].strip()

def get_wordnet_lexicographer_files():
    global lexicographer_files
    lexicographer_files = {}
    with open('resources/wordnet/lexicographer_files.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter='\t')
        for row in csv_reader:
            if len(row) > 2:
                lexicographer_files[row[0]] = {
                    "name": row[1].strip(),
                    "contents": row[2].strip(),
                    "permitted": row[3].strip()
                }

def open_csvs():
    global f_wordnet_synset_file, f_wordnet_term_file, f_wordnet_relation_file
    load_dotenv('.env')
    wordnet_synset_file = os.path.join(os.getcwd(), "resources", "wordnet", "temp", os.getenv('WORDNET_SYNSET_FILE'))
    wordnet_term_file = os.path.join(os.getcwd(), "resources", "wordnet", "temp", os.getenv('WORDNET_TERM_FILE'))
    wordnet_relation_file = os.path.join(os.getcwd(), "resources", "wordnet", "temp", os.getenv('WORDNET_RELATION_FILE'))
    
    f_wordnet_synset_file = open(wordnet_synset_file, "w")
    f_wordnet_term_file = open(wordnet_term_file, "w")
    f_wordnet_relation_file = open(wordnet_relation_file, "w")

def decapitalize(s):
    if not s:  # check that s is not empty string
        return s
    return s[0].lower() + s[1:]

def left(s, amount):
    return s[:amount]

def right(s, amount):
    return s[-amount:]

def mid(s, offset, amount):
    return s[offset:offset+amount]

def cleanse(s):
    s = s.replace("(", "")
    s = s.replace(")", "")
    s = s.replace("“", '"')
    s = s.replace("”", '"')
    s = s.replace("‘", "'")
    s = s.replace("’", "'")
    s = s.replace(r'\\u00e9', "é")
    s = s.strip("'")
    s = s.strip('"')
    s = s.strip(',')
    return s
