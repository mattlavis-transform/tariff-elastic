from punctuation import Punctuation
from nltk.stem import PorterStemmer
import os
import sys
import json
import classes.globals as g


class Expander:
    def __init__(self, facet, lexemes, description):
        self.classifier_folder = os.path.join(os.getcwd(), "resources", "facet_classifiers")
        self.facet = facet
        self.lexemes = lexemes
        self.description = description
        self.terms = []

        self.get_terms()

    def get_terms(self):
        # In which we loop through the 'training' JSON files for all of the standard classifiers
        # to assign facets against comm codes, to be used for filtering and tagging
        # standard_classifiers = [
        #     "animal_type",
        #     "animal_product_state",
        #     "animal_purpose",
        #     "bone_state",
        #     "fish_classification",
        #     "fat_content",
        #     "dairy_form",
        #     "cheese_type",
        #     "egg_shell_status",
        #     "egg_purpose",
        #     "plant_state",
        #     "fruit_vegetable_state",
        #     "nut_state",
        #     "coffee_state",
        #     "herb_spice_state",
        #     "cereal_state",
        #     "flour_source",
        #     "oil_fat_source",
        #     "margarine_state",
        #     "fish_preparation",
        #     "sugar_state",
        #     "cocoa_state",
        #     "pasta_state",
        #     "bread_type",
        #     "jam_sugar_content",
        #     "jam_ingredient",
        #     "fruit_spirit",
        #     "juice_ingredient"
        #     "brix_value",
        #     "beverage_type",
        #     "wine_type",
        #     "alcohol_volume",
        #     "wine_origin",
        #     "tobacco_type",
        #     "clothing_gender",
        #     "garment_type",
        #     "garment_material",
        #     "computer_type"
        # ]
        for classifier in g.taxonomiser.facets_dict:
            if self.facet == classifier:
                self.classify_against(classifier)

    def classify_against(self, facet):
        filename = "classifier_" + facet + ".json"
        path = os.path.join(self.classifier_folder, filename)
        if os.path.exists(path):
            with open(path) as json_file:
                filter_options = json.load(json_file)
                for filter in filter_options:
                    self.term_check(filter, facet)
        else:
            print("\nCLASSIFICATION CANNOT COMPLETE: File {filename} cannot be found\n".format(filename=filename))
            sys.exit()

    def term_check(self, filter, facet):
        # This will check against the verbatim in the description
        # if there is more than one word in the term
        # And against the stemmed lexemes if there is just one word.
        my_porter = PorterStemmer()
        key_terms_stemmed = []
        verbatim_match = False
        for key in filter:  # there is only one key, but this is the only way to access it
            if facet == "fat_content":
                if self.description == "exceeding 21% but not exceeding 45%":
                    a = 1
            key_terms = filter[key]
            for term in key_terms:
                if len(term.split()) > 1:
                    if term in self.description:
                        if "not" not in term and "not" in self.description:
                            verbatim_match = False
                        else:
                            verbatim_match = True
                            break

                term_stemmed = my_porter.stem(term)
                key_terms_stemmed.append(term_stemmed)

            intersection_set = set.intersection(set(key_terms_stemmed), set(self.lexemes))

            term_found = True if (len(intersection_set) > 0 or verbatim_match) else False
            if term_found:
                self.terms.append(key)