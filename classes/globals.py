import csv
from datetime import datetime
from dotenv import load_dotenv
import string

from classes.taxonomiser import Taxonomiser

taxonomiser = Taxonomiser()
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


def decapitalize(s):
    if not s:  # check that s is not empty string
        return s
    return s[0].lower() + s[1:]


def left(s, amount):
    return s[:amount]


def right(s, amount):
    return s[-amount:]


def mid(s, offset, amount):
    return s[offset:offset + amount]


def cleanse(s, classification_class=None):
    if classification_class == "chapter":
        s = left(s, 1).upper() + right(s, len(s) - 1).lower()

    # s = s.replace("(", "")
    # s = s.replace(")", "")
    s = s.replace("“", '"')
    s = s.replace("”", '"')
    s = s.replace("‘", "'")
    s = s.replace("’", "'")
    s = s.replace(r'\\u00e9', "é")
    s = s.replace("\u00a0", " ")
    s = s.strip()
    return s


def date_format(s):
    if s == "":
        s = None
        s = "2099-12-31"
    else:
        s = datetime.strptime(s, '%d/%m/%Y').strftime('%Y-%m-%d')
    return s


def cleanse_friendly_name(s):
    if "excl." in s:
        a = 1
    s = s.lower()
    s = s.replace("excl.", "excluding")
    exclude = set(string.punctuation)
    s = ''.join(ch for ch in s if ch not in exclude)
    exclusion_terms = [
        "neither",
        "other than",
        "excluding",
        "not including",
        "except for",
        " not "
    ]
    for exclusion_term in exclusion_terms:
        if exclusion_term in s:
            s = s.split(exclusion_term)[0]
            break

    return s.strip()
