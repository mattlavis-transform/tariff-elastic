import json
import os
import re
from dotenv import load_dotenv
from stop_words import get_stop_words
from punctuation import Punctuation
from nltk.stem import PorterStemmer
from classes.entity_mapper import EntityMapper

from classes.expander import Expander


class Commodity:
    # This class is used in the taxonimiser, not in generating the search corpus
    def __init__(self, row):
        self.sid = int(row[0])
        self.goods_nomenclature_item_id = row[1]
        if self.goods_nomenclature_item_id == "8528420000":
            a = 1
        self.productline_suffix = row[2]
        self.start_date = row[3]
        self.end_date = row[4]
        self.number_indents = int(row[5])
        if self.number_indents == 0 and self.goods_nomenclature_item_id[2:10] == "00000000":
            self.number_indents = -1
        self.leaf = int(row[6])
        self.description = row[7]
        self.classification = row[8]
        self.hierarchy_string = row[10]

        self.description_original = self.description
        self.heading = self.goods_nomenclature_item_id[0:4]
        if self.goods_nomenclature_item_id[-8:] != "00000000":
            self.number_indents += 1

        self.lexemes = []
        self.hierarchy = []
        self.facets = {}

        self.shed_excluding()
        self.make_lexemes()
        self.get_weight_size_and_volume()

    def make_lexemes(self):
        # Uses the NLTK Porter Stemmer to find the stem words in the term
        # It also excludes any stop words, such that irrelevant stuff is not indexed
        # Adds any found stem terms to 'lexemes'

        self.description = self.description.replace("\xa0", " ")
        self.description = self.description.replace(" %", "prozent")
        my_porter = PorterStemmer()
        self.description = Punctuation.remove(self.description).lower()
        self.description = self.description.replace("prozent", "%")
        self.combine_special_words()
        stop_words = get_stop_words('en')
        try:
            stop_words.remove("other")
        except Exception as e:
            pass
        parts = self.description.split()
        for part in parts:
            if part not in stop_words:
                part_stemmed = my_porter.stem(part)
                self.lexemes.append(part_stemmed)

        self.lexemes.append(self.goods_nomenclature_item_id)
        self.lexemes.append(self.goods_nomenclature_item_id[0:4])
        self.lexemes.append(self.goods_nomenclature_item_id[0:6])
        self.lexemes.append(self.hierarchy_string)

    def combine_special_words(self):
        load_dotenv('.env')
        self.special_words_file = os.getenv('SPECIAL_WORDS_FILE')
        self.special_words_file = os.path.join(os.getcwd(), "resources", "special_words", self.special_words_file)
        with open(self.special_words_file) as json_file:
            data = json.load(json_file)
            for term in data['hyphenate']:
                self.description = self.description.replace(term, term.replace(" ", "-"))
            for item in data['replace']:
                self.description = self.description.replace(item["from"], item["to"])

    def shed_excluding(self):
        exclusion_terms = [
            "neither",
            "other than",
            "excluding",
            "not including",
            "except for"
        ]
        for exclusion_term in exclusion_terms:
            if exclusion_term in self.description.lower():
                if ";" not in self.description:
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
        for facet in facets:
            if facet == "entity":
                entity_mapper = EntityMapper(self.goods_nomenclature_item_id)
                self.facets["entity"] = entity_mapper.mapped_entity
            else:
                expander = Expander(facet, self.lexemes, self.description_original, self.goods_nomenclature_item_id)
                if len(expander.terms) > 0:
                    self.facets[facet] = expander.terms

    def get_weight_size_and_volume(self):
        weights_include = [
            {
                'term': 'of a weight',
                'case_sensitivity': 'insensitive'
            },
            {
                'term': 'gross vehicle weight',
                'case_sensitivity': 'insensitive'
            },
            {
                'term': 'of an unladen weight',
                'case_sensitivity': 'insensitive'
            },
            {
                'term': 'unladen (net) weight',
                'case_sensitivity': 'insensitive'
            },
            {
                'term': 'packings of a content',
                'case_sensitivity': 'insensitive'
            },
            {
                'term': 'packings of a net content',
                'case_sensitivity': 'insensitive'
            },
            {
                'term': 'weighing',
                'case_sensitivity': 'insensitive'
            },
            {
                'term': 'a weight of',
                'case_sensitivity': 'insensitive'
            },
            {
                'term': 'unfilled weight',
                'case_sensitivity': 'insensitive'
            },
            {
                'term': 'of a net weight',
                'case_sensitivity': 'insensitive'
            },
            {
                'term': 'of a gross weight',
                'case_sensitivity': 'insensitive'
            },
            {
                'term': 'Exceeding',
                'case_sensitivity': 'sensitive'
            },
            {
                'term': 'Not exceeding',
                'case_sensitivity': 'sensitive'
            },
            {
                'term': 'of a net capacity',
                'case_sensitivity': 'insensitive'
            }
        ]
        self.description_lower = self.description.lower()
        for term in weights_include:
            a = 1
            if term["case_sensitivity"] == 'insensitive':
                if term["term"].lower() in self.description_lower:
                    self.process_weight(term)
            else:
                if term["term"] in self.description:
                    self.process_weight(term)

    def process_weight(self, term):
        self.weight_lower = None
        self.weight_upper = None

        # Get "not exceeding for upper bounds"
        match = re.search("not exceeding ([0-9, ]{1,6} kg|tonnes|g)", self.description_lower)
        if match:
            groups = match.groups()
            if len(groups) > 0:
                my_value = groups[0]
                self.weight_upper = self.process_weight_unit(my_value)

        # Get "weight exceeding for upper bounds"
        match = re.search("weight exceeding ([0-9,]{1,6} kg|tonnes|g)", self.description_lower)
        if match:
            groups = match.groups()
            if len(groups) > 0:
                my_value = groups[0]
                self.weight_lower = self.process_weight_unit(my_value)

    def process_weight_unit(self, my_value):
        stripped = my_value.replace(" kg", "").replace(" tonnes", "").replace(" g", "").strip().replace(" ", "")
        if " kg" in my_value:
            multiplier = 1
        elif " g" in my_value:
            multiplier = 0.001
        else:
            multiplier = 1000
        processed_value = float(stripped) * multiplier
        return processed_value

    def inherit_facets(self):
        # Loop through all of the antecedents for the current commodity. If there is
        # no facet defined on the current commodity, then loop up through the
        # commodity's hierarchy until you find a commodity which does have a value
        # in the same facet. Use that facet then break

        for antecedent in self.hierarchy:
            for facet in antecedent.facets:
                if facet not in self.facets:
                    self.facets[facet] = antecedent.facets[facet]

        # for my_facet in self.facets:
        #     if len(self.facets[my_facet]) == 0:
        #         for antecedent in self.hierarchy:
        #             f = antecedent.facets
        #             if my_facet in antecedent.facets:
        #                 if len(antecedent.facets[my_facet]) > 0:
        #                     self.facets[my_facet] = antecedent.facets[my_facet]
        #                     break
