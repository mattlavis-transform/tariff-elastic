from punctuation import Punctuation
from nltk.stem import PorterStemmer
import os
import sys
import json
import classes.globals as g


class EntityMapper:
    def __init__(self, goods_nomenclature_item_id):
        self.classifier_folder = os.path.join(os.getcwd(), "resources", "facet_classifiers")
        self.goods_nomenclature_item_id = goods_nomenclature_item_id
        self.mapped_entity = ""

        filename = "classifier_entity.json"
        path = os.path.join(self.classifier_folder, filename)
        if os.path.exists(path):
            with open(path) as json_file:
                filter_options = json.load(json_file)
                for filter in filter_options:
                    if self.mapped_entity == "":
                        for key in filter:
                            categories = filter[key]
                            for category in categories:
                                category_length = len(category)
                                if goods_nomenclature_item_id[0:category_length] == category:
                                    self.mapped_entity = key
                                    break
                    else:
                        break

        a = 1
