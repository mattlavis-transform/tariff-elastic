import os
import json
import string
from dotenv import load_dotenv
from punctuation import Punctuation
import classes.functions as funcs


class Classification(object):
    def __init__(self, row=None, nlp=None):
        self.sid = None
        self.goods_nomenclature_item_id = ""
        self.productline_suffix = ""
        self.validity_start_date = ""
        self.validity_end_date = ""
        self.indent = None
        self.end_line = None
        self.description = ""
        self.description_indexed = ""
        self.description_friendly = ""
        self.classification_class = ""
        self.goods_nomenclature_item_id_plus_pls = ""
        self.hierarchy_string = ""
        self.parent_sid = None
        self.friendly_name = ""

        self.hierarchy = []
        self.full_hierarchy = []
        self.siblings = []
        self.search_references = []

        if row is not None:
            self.row = row
            self.sid = int(row[0])
            self.goods_nomenclature_item_id = row[1]
            self.productline_suffix = row[2]
            self.comm_code_plus_pls = self.goods_nomenclature_item_id + "_" + self.productline_suffix
            self.validity_start_date = funcs.date_format(row[3])
            self.validity_end_date = funcs.date_format(row[4])
            self.indent = int(row[5])
            self.end_line = int(row[6])
            self.classification_class = row[8]
            self.description = funcs.cleanse(row[7], self.classification_class)
            self.goods_nomenclature_item_id_plus_pls = row[9]
            self.hierarchy_string = row[10]
            self.parent_comm_code_plus_pls = None
            self.nlp = nlp
            self.terms = {}

            del self.row

            self.combine_special_words()
            self.expand_hierarchy_string()
            self.get_spacy_terms()

    def get_spacy_terms(self):
        # print(self.goods_nomenclature_item_id)
        doc = self.nlp(self.description)

        self.terms = {
            "chunks": [],
            "nouns": [],
            "verbs": [],
            "adjectives": [],
            "dependencies": []
        }

        self.terms["chunks"] = [chunk.text.lower() for chunk in doc.noun_chunks]
        self.terms["nouns"] = [token.lemma_.lower() for token in doc if token.pos_ == "NOUN"]
        self.terms["verbs"] = [token.lemma_.lower() for token in doc if token.pos_ == "VERB"]
        self.terms["adjectives"] = [token.lemma_.lower() for token in doc if token.pos_ == "ADJ"]

        self.nouns = " ".join(token.lemma_.lower() for token in doc if token.pos_ == "NOUN")
        self.chunks = " ".join(chunk.text.lower() for chunk in doc.noun_chunks)
        self.adjectives = " ".join(token.lemma_.lower() for token in doc if token.pos_ == "ADJ")
        a = 1

        # Analyze syntax
        self.dependencies = []
        for token in doc:
            dependency = {
                token.text: [token.dep_]
            }
            self.dependencies.append(dependency)

        # self.terms["dependencies"] = self.dependencies

    def expand_hierarchy_string(self):
        # This hierarchy string is derived from the CSV file already: it is not worked out in this application
        # This does not add in the description into the hierarchy though (that comes later)
        self.hierarchy_dict = {}
        if self.hierarchy_string != "":
            parts = self.hierarchy_string.split(",")
            if len(parts) > 0:
                parts = list(reversed(parts))
                for part in parts:
                    string_parts = part.split("_")  # Splits the hierarchy instance into the commodity code and the product line suffix
                    c = Classification(row=None)
                    c.goods_nomenclature_item_id = string_parts[0]
                    c.productline_suffix = string_parts[1]
                    c.goods_nomenclature_item_id_plus_pls = part
                    self.hierarchy_dict[part] = c

    def get_facet_assignments(self, facet_assignments):
        self.assignments = {}
        if self.sid in facet_assignments:
            assignments = facet_assignments[self.sid]
            for assignment in assignments:
                self.assignments[assignment["filter_name"]] = assignment["value"]

    def generate_indexed_description(self):
        # self.description_indexed = Punctuation.remove(self.description).lower()
        self.description_indexed = self.description
        exclusion_terms = [
            "neither",
            "other than",
            "excluding",
            "not including",
            "except for"
        ]
        for exclusion_term in exclusion_terms:
            if exclusion_term in self.description_indexed.lower():
                if ";" not in self.description_indexed:
                    self.description_indexed = self.description_indexed.split(exclusion_term)[0]
                    exit
        self.description_indexed = self.description_indexed.strip()
        self.description_indexed = self.description_indexed.strip(",")
        self.description_indexed = self.description_indexed.strip("(")
        self.description_indexed = self.description_indexed.strip()

    def get_search_references(self, search_references_dict):
        if self.goods_nomenclature_item_id in search_references_dict:
            self.search_references = search_references_dict[self.goods_nomenclature_item_id]

    def get_chapter_heading(self):
        if self.classification_class == "chapter":
            self.chapter = None
            self.heading = None
        elif self.classification_class == "heading":
            self.chapter = self.hierarchy[0]
            self.heading = None
        else:
            self.chapter = self.hierarchy[0]
            self.heading = self.hierarchy[1]

    def get_full_hierarchy_json(self):
        self.hierarchy_json = []
        for hier in self.full_hierarchy:
            item = {
                "goods_nomenclature_item_id": hier.goods_nomenclature_item_id,
                "productline_suffix": hier.productline_suffix,
                "class": hier.classification_class,
                "description": hier.description_indexed
            }
            self.hierarchy_json.append(item)

    def write(self, dest_folder):
        if self.description_indexed == "":
            self.description_indexed = self.description

        self.filename = os.path.join(dest_folder, self.goods_nomenclature_item_id + self.productline_suffix + ".json")
        self.json = {}
        self.json["sid"] = self.sid
        self.json["goods_nomenclature_item_id"] = self.goods_nomenclature_item_id
        self.json["heading_id"] = self.goods_nomenclature_item_id[0:4]
        self.json["chapter_id"] = self.goods_nomenclature_item_id[0:2]
        self.json["productline_suffix"] = self.productline_suffix
        self.json["class"] = self.classification_class
        self.json["description"] = self.description
        self.json["description_indexed"] = self.description_indexed
        self.json["description_friendly"] = self.description_friendly
        self.json["chapter"] = self.chapter
        self.json["heading"] = self.heading
        self.json["hierarchy"] = self.hierarchy_json
        self.json["search_references"] = self.search_references
        self.json["validity_start_date"] = self.validity_start_date
        self.json["validity_end_date"] = self.validity_end_date
        # self.json["terms"] = self.terms
        self.json["nouns"] = self.nouns
        self.json["chunks"] = self.chunks
        self.json["adjectives"] = self.adjectives

        # Add in the custom assignments if they exist
        for key, value in self.assignments.items():
            self.json[key] = value

        # Add in ancestry
        if self.goods_nomenclature_item_id == "9207101000":
            a = 1

        for i in range(0, 12):
            if len(self.hierarchy) > i:
                self.json["ancestor_" + str(i)] = self.hierarchy[i]

        with open(self.filename, 'w') as outfile:
            json.dump(self.json, outfile, indent=4)

    # def check_parent_of_other(self):
    #     parent = self.hierarchy[0].lower()
    #     exclude = set(string.punctuation)
    #     parent = ''.join(ch for ch in parent if ch not in exclude)
    #     parent_parts = parent.split()
    #     for element in parent_parts:
    #         if element in g.app.stopwords:
    #             parent_parts.remove(element)

    #     parent_modified = parent
    #     for sibling in self.siblings:
    #         tmp = sibling.lower()
    #         parent_modified = parent_modified.replace(tmp, "")

    #     if parent_modified != parent:
    #         parent_modified = parent_modified.replace(" ,", ",")
    #         parent_modified = parent_modified.replace(", , ", ", ")
    #         parent_modified = parent_modified.replace(",, ", ",")
    #         parent_modified = parent_modified.replace(",", " ")
    #         parent_modified = parent_modified.capitalize()
    #         if parent_modified.lower() != parent.lower():
    #             return parent_modified
    #         else:
    #             return ""
    #     else:
    #         return ""

    def combine_special_words(self):
        if self.goods_nomenclature_item_id == "6201200011":
            a = 1
        load_dotenv('.env')
        self.database_url = os.getenv('DATABASE_UK')
        self.special_words_file = os.getenv('SPECIAL_WORDS_FILE')
        self.special_words_file = os.path.join(os.getcwd(), "resources", "special_words", self.special_words_file)
        with open(self.special_words_file) as json_file:
            data = json.load(json_file)
            for term in data['hyphenate']:
                self.description = self.description.replace(term, term.replace(" ", "-"))
            for item in data['replace']:
                self.description = self.description.replace(item["from"], item["to"])
