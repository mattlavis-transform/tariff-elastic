import json
import os
from dotenv import load_dotenv
from stop_words import get_stop_words
from punctuation import Punctuation
from nltk.stem import PorterStemmer

from classes.expander import Expander


class Commodity:
    def __init__(self, row):
        self.sid = int(row[0])
        self.goods_nomenclature_item_id = row[1]
        self.productline_suffix = row[2]
        self.start_date = row[3]
        self.end_date = row[4]
        self.number_indents = int(row[5])
        if self.number_indents == 0 and self.goods_nomenclature_item_id[2:10] == "00000000":
            self.number_indents = -1
        self.leaf = int(row[6])
        self.description = row[7]
        self.classification = row[8]

        self.description_original = self.description
        self.heading = self.goods_nomenclature_item_id[0:4]
        if self.goods_nomenclature_item_id[-8:] != "00000000":
            self.number_indents += 1

        self.lexemes = []
        self.hierarchy = []
        self.facets = {}

        self.shed_excluding()
        self.make_lexemes()

    def make_lexemes(self):
        # Uses the NLTK Porter Stemmer to find the stem words in the term
        # It also excludes any stop words, such that irrelevant stuff is not indexed
        # Adds any found stem terms to 'lexemes'
        if self.goods_nomenclature_item_id == "0401100000":
            a = 1
        self.description = self.description.replace("\xa0", " ")
        self.description = self.description.replace(" %", "prozent")
        my_porter = PorterStemmer()
        self.description = Punctuation.remove(self.description).lower()
        self.description = self.description.replace("prozent", "%")
        self.combine_special_words()
        stop_words = get_stop_words('en')
        parts = self.description.split()
        for part in parts:
            if part not in stop_words:
                part_stemmed = my_porter.stem(part)
                self.lexemes.append(part_stemmed)

        self.lexemes.append(self.goods_nomenclature_item_id)

    def combine_special_words(self):
        return
        load_dotenv('.env')
        self.database_url = os.getenv('DATABASE_UK')
        self.special_words_file = os.getenv('SPECIAL_WORDS_FILE')
        self.special_words_file = os.path.join(os.getcwd(), "resources", "source", self.special_words_file)
        with open(self.special_words_file) as json_file:
            data = json.load(json_file)
            for term in data['hyphenate']:
                self.description = self.description.replace(term, term.replace(" ", "-"))

    def shed_excluding(self):
        if self.goods_nomenclature_item_id == "0102291030":
            a = 1
        exclusion_terms = [
            "neither",
            "other than",
            "excluding",
            "not including",
            "except for",
            " not "
        ]
        for exclusion_term in exclusion_terms:
            if exclusion_term in self.description.lower():
                self.description = self.description.split(exclusion_term)[0]
                exit

    def get_row(self):
        s = []
        s.append(self.goods_nomenclature_item_id)
        s.append(self.productline_suffix)
        s.append(self.description)
        s.append(self.number_indents)
        s.append(self.leaf)
        return s

    def expand_facets(self, facets):
        if self.goods_nomenclature_item_id == "0102291000":
            a = 1
        for facet in facets:
            expander = Expander(facet, self.lexemes, self.description_original)
            self.facets[facet] = expander.terms

    def inherit_facets(self):
        # Loop through all of the antecedents for the current commodity. If there is
        # no facet defined on the current commodity, then loop up through the
        # commodity's hierarchy until you find a commodity which does have a value
        # in the same facet. Use that facet then break
        for my_facet in self.facets:
            if len(self.facets[my_facet]) == 0:
                for antecedent in self.hierarchy:
                    f = antecedent.facets
                    if my_facet in antecedent.facets:
                        if len(antecedent.facets[my_facet]) > 0:
                            self.facets[my_facet] = antecedent.facets[my_facet]
                            break
