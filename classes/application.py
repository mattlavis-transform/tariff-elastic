import re
import os
import sys
import fileinput
import csv
import json
import ndjson
import requests
from dotenv import load_dotenv
from classes.classification import Classification
from classes.search_reference import SearchReference
from classes.synonym import Synonym
import classes.functions as funcs
import spacy
from spacy.tokens import Doc

class Application(object):
    def __init__(self):
        load_dotenv('.env')
        self.facets_export_folder = os.path.join(os.getcwd(), "resources", "facets_export")
        self.facets_export_file = os.path.join(self.facets_export_folder, os.getenv("FACETS_EXPORT_FILE"))
        self.include_search_refs = int(os.getenv('INCLUDE_SEARCH_REFS'))
        self.commodity_file = os.getenv('COMMODITY_MASTER')
        self.friendly_descriptions_file = os.getenv('FRIENDLY_DESCRIPTIONS_FILE')
        self.dest_folder = os.path.join(os.getcwd(), "resources", "json")
        self.stopwords_file = os.path.join(os.getcwd(), "resources", os.getenv('STOPWORDS_FILE'))
        self.synonyms_file = os.path.join(os.getcwd(), "resources", os.getenv('SYNONYMS_FILE'))
        self.commodities_filename1 = os.path.join("resources", "ndjson", "commodities1.ndjson")
        self.commodities_filename2 = os.path.join("resources", "ndjson", "commodities2.ndjson")

        self.commodity_minimum = os.getenv('COMMODITY_MINIMUM')
        self.commodity_maximum = os.getenv('COMMODITY_MAXIMUM')

        self.load_spacy()

    def load_spacy(self):
        # self.nlp = spacy.load("en_core_web_sm")
        self.nlp = spacy.load("en_core_web_md")
        self.introduce_tariff_pipeline()
        a = 1

    def introduce_tariff_pipeline(self):
        self.initialise_attributes()
        # Get the Spacy pattern data from the pattern file
        filename = os.path.join(os.getcwd(), "resources", "patterns", "patterns.json")
        f = open(filename)
        self.spacy_patterns = json.load(f)
        f.close()

        ruler = self.nlp.add_pipe("entity_ruler", before="ner")
        ruler.add_patterns(self.spacy_patterns)
        # doc = nlp(text)
        # for ent in doc.ents:
        #     print(ent.text, ent.label_)

    def initialise_attributes(self):
        Doc.set_extension("age", default=None)
        a = 1

    def generate_es_corpus(self):
        self.load_synonyms()
        self.load_stopwords()
        self.get_search_references()
        self.get_facet_assignments()
        self.load_commodity_code_data()
        self.write_search_references()
        self.inherit_facet_assignments()
        self.apply_facet_assignments_to_commodities()
        self.generate_indexed_description()
        self.get_hierarchy_node()
        self.inherit_spacy_terms()
        self.get_siblings()
        self.get_others()
        self.process_data()
        self.write_commodities_ndjson_file()
        self.insert_blank_index_lines()
        self.complete()

    def load_synonyms(self):
        print("Getting synonyms")
        f = open(self.synonyms_file)
        self.synonyms_json = json.load(f)["data"]["synonyms"]
        f.close()
        self.parse_synonyms()
        print("- Complete\n")

    def parse_synonyms(self):
        self.synonyms = []
        for synonym_raw in self.synonyms_json:
            synonym = Synonym(synonym_raw)
            self.synonyms.append(synonym)
        self.create_synonym_dictionary()

    def load_stopwords(self):
        print("Getting stopwords")
        f = open(self.stopwords_file)
        self.stopwords = json.load(f)
        self.stopwords = self.stopwords
        f.close()
        print("- Complete\n")

    def get_search_references(self):
        print("Getting search references")
        self.search_references = []
        self.search_references_dict = {}
        alphabet = "abcdefghijklmnopqrstuvwxyz"
        for i in range(0, len(alphabet)):
            letter = alphabet[i:i + 1]
            url = "https://www.trade-tariff.service.gov.uk/api/v2/search_references.json?query[letter]=" + letter
            response = requests.get(url)
            data = response.json()["data"]
            for item in data:
                search_reference = SearchReference(item)
                if search_reference.title == "pizza":
                    a = 1
                self.search_references.append(search_reference)
                if search_reference.goods_nomenclature_item_id in self.search_references_dict:
                    self.search_references_dict[search_reference.goods_nomenclature_item_id].append(search_reference.title)
                else:
                    self.search_references_dict[search_reference.goods_nomenclature_item_id] = [search_reference.title]

        self.search_references = sorted(self.search_references, key=lambda x: int(x.goods_nomenclature_item_id))
        print("- Complete\n")

    def write_search_references(self):
        filename = os.path.join(os.getcwd(), "resources", "search_references.csv")
        f = open(filename, 'w')
        writer = csv.writer(f)
        row = [
            "goods_nomenclature_item_id",
            "productline_suffix",
            "referenced_class",
            "title",
            "indent"
        ]
        writer.writerow(row)

        for search_reference in self.search_references:
            lookup = search_reference.goods_nomenclature_item_id + "_" + search_reference.productline_suffix
            try:
                search_reference.indent = self.classification_dict[lookup].indent
            except Exception as e:
                search_reference.indent = None

            row = [
                search_reference.goods_nomenclature_item_id,
                search_reference.productline_suffix,
                search_reference.referenced_class,
                search_reference.title,
                search_reference.indent
            ]
            a = 1
            writer.writerow(row)
        f.close()

    def apply_facet_assignments_to_commodities(self):
        print("Assigning facet assignments to commodities")
        for c in self.classifications:
            c.get_facet_assignments(self.facet_assignments)
        print("- Complete\n")

    def get_facet_assignments(self):
        print("Getting facet assignments")
        with open(self.facets_export_file) as f:
            facet_assignments = ndjson.load(f)
            self.facet_assignments = {}
            for item in facet_assignments:
                sid = item["goods_nomenclature_sid"]
                if sid in self.facet_assignments:
                    self.facet_assignments[sid].append(item)
                else:
                    self.facet_assignments[sid] = [item]
        print("- Complete\n")

    def inherit_facet_assignments(self):
        print("Inheriting down facet assignments")
        for i in range(0, len(self.classifications)):
            c = self.classifications[i]
            if c.sid in self.facet_assignments:
                for j in range(i + 1, len(self.classifications)):
                    c2 = self.classifications[j]
                    if c2.indent <= c.indent:
                        break
                    else:
                        if c2.sid not in self.facet_assignments:
                            self.facet_assignments[c2.sid] = self.facet_assignments[c.sid]

        print("- Complete\n")

    def create_synonym_dictionary(self):
        self.synonyms_dict = {}
        for synonym in self.synonyms:
            if synonym.bi_directional:
                for term in synonym.terms:
                    for term2 in synonym.terms:
                        if term != term2:
                            if term in self.synonyms_dict:
                                self.synonyms_dict[term].append(term2)
                            else:
                                self.synonyms_dict[term] = [term2]

    def load_commodity_code_data(self):
        # Reads in all of the commodity codes from the specified CSV file
        # In reality, this should come from the database

        print("Reading commodity code data from CSV")
        self.classifications = []
        self.classification_dict = {}
        with open(self.commodity_file) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            for row in csv_reader:
                if line_count > 0:
                    goods_nomenclature_item_id = row[1]
                    if goods_nomenclature_item_id >= self.commodity_minimum and goods_nomenclature_item_id <= self.commodity_maximum:
                        classification = Classification(row, self.nlp)
                        self.classifications.append(classification)
                        self.classification_dict[classification.goods_nomenclature_item_id_plus_pls] = classification
                line_count += 1

                # if line_count > 100:
                #     break

        print(f'- Complete: processed {line_count} lines of the goods classification.\n')

    def get_hierarchy_node(self):
        for classification in self.classifications:
            if classification.goods_nomenclature_item_id == "9207101000":
                a = 1
            classification.hierarchy_json = []
            if len(classification.hierarchy_dict) > 0:
                for hierarchy_tier in classification.hierarchy_dict:
                    classification.hierarchy_dict[hierarchy_tier].sid = self.classification_dict[hierarchy_tier].sid
                    classification.hierarchy_dict[hierarchy_tier].description_indexed = self.classification_dict[hierarchy_tier].description_indexed
                    classification.hierarchy_dict[hierarchy_tier].classification_class = self.classification_dict[hierarchy_tier].classification_class
                    item = {
                        "sid": classification.hierarchy_dict[hierarchy_tier].sid,
                        "goods_nomenclature_item_id": classification.hierarchy_dict[hierarchy_tier].goods_nomenclature_item_id,
                        "productline_suffix": classification.hierarchy_dict[hierarchy_tier].productline_suffix,
                        "class": classification.hierarchy_dict[hierarchy_tier].classification_class,
                        "description": classification.hierarchy_dict[hierarchy_tier].description_indexed
                    }
                    classification.hierarchy_json.append(item)
                    classification.hierarchy.append(classification.hierarchy_dict[hierarchy_tier].description_indexed)

    def inherit_spacy_terms(self):
        a = 1

    def get_siblings(self):
        classification_count = len(self.classifications)
        self.parent_list = {}

        for loop1 in range(0, classification_count - 1):
            c1 = self.classifications[loop1]
            for loop2 in range(loop1 + 1, classification_count):
                c2 = self.classifications[loop2]
                if c2.indent == c1.indent + 1:
                    self.classifications[loop2].parent_sid = c1.sid
                    self.classifications[loop2].parent_comm_code_plus_pls = c1.comm_code_plus_pls
                    if c1.comm_code_plus_pls in self.parent_list:
                        self.parent_list[c1.comm_code_plus_pls].append(c2.comm_code_plus_pls)
                    else:
                        self.parent_list[c1.comm_code_plus_pls] = [c2.comm_code_plus_pls]
                elif c2.indent <= c1.indent:
                    break

        for classification in self.classifications:
            if classification.parent_comm_code_plus_pls is not None:
                for item in self.parent_list[classification.parent_comm_code_plus_pls]:
                    if item != classification.comm_code_plus_pls:
                        classification.siblings.append(item)

    def lower_first(self, s):
        ret = s[:1].lower() + s[1:]
        return ret

    def generate_indexed_description(self):
        for classification in self.classifications:
            classification.generate_indexed_description()

    def get_others(self):
        # Description is the verbatim
        # Description_indexed is what gets indexed
        # Description_friendly is this: not sure if it has a value yet
        self.singles = []
        self.multiples = []
        for classification in self.classifications:
            classification.description_friendly = classification.description
            if len(classification.siblings) == 1:
                if classification.description == "Other":
                    classification.description_friendly = "Other than " + self.lower_first(self.classification_dict[classification.siblings[0]].description)
                    self.singles.append({
                        "key": classification.comm_code_plus_pls,
                        "was": classification.description,
                        "is": classification.description_friendly
                    })
            elif len(classification.siblings) > 1:
                if classification.description == "Other":
                    classification.description_friendly = self.classification_dict[classification.parent_comm_code_plus_pls].description_friendly
                    alternatives = ""
                    for sibling in classification.siblings:
                        desc = self.classification_dict[sibling].description
                        if "Heifers" in desc:
                            a = 1
                        desc = re.sub("\([^\)]+\)", "", desc)
                        desc = desc.replace("  ", "").strip()
                        alternatives += self.lower_first(desc) + " / "
                    alternatives = alternatives.strip()
                    alternatives = alternatives.strip("/")
                    alternatives = alternatives.strip()

                    classification.description_friendly += " (excluding {alternatives})".format(alternatives=alternatives)

                    self.multiples.append({
                        "key": classification.comm_code_plus_pls,
                        "description": classification.description,
                        "description_indexed": classification.description_indexed,
                        "description_friendly": classification.description_friendly,
                        "sibling_count": len(classification.siblings)
                    })

        print("Generating a list of 'Others' that have just one sibling")
        with open('single_siblings.csv', 'w',) as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Key', 'Was', 'Is'])
            for item in self.singles:
                writer.writerow(
                    [item["key"],
                     item["was"],
                     item["is"]]
                )

        print("Generating a list of 'Others' that have just multiple siblings")
        with open('multiple_siblings.csv', 'w',) as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Key', 'Description', 'Description alternative', 'Parent', 'Sibling count'])
            for item in self.multiples:
                writer.writerow(
                    [item["key"],
                     item["description"],
                     item["description_indexed"],
                     item["sibling_count"]]
                )

    def process_data(self):
        for classification in self.classifications:
            classification.get_search_references(self.search_references_dict)

    def write_commodities_ndjson_file(self):
        ndjson_list1 = []
        ndjson_list2 = []
        index = 0
        classification_count = len(self.classifications)
        for classification in self.classifications:
            index += 1
            classification.get_chapter_heading()
            classification.write(self.dest_folder)
            if index < classification_count / 2:
                ndjson_list1.append(classification.json)
            else:
                ndjson_list2.append(classification.json)

        # Check if commodities filename 1 exists
        file_exists = os.path.exists(self.commodities_filename1)
        if file_exists:
            os.remove(self.commodities_filename1)

        # Check if commodities filename 2 exists
        file_exists = os.path.exists(self.commodities_filename2)
        if file_exists:
            os.remove(self.commodities_filename2)

        # Write the 1st file
        with open(self.commodities_filename1, 'w') as f:
            f.write('\n')
            ndjson.dump(ndjson_list1, f)

        # Write the 2nd file
        with open(self.commodities_filename2, 'w') as f:
            f.write('\n')
            ndjson.dump(ndjson_list2, f)

    def insert_blank_index_lines(self):
        # The line { "index": {} } is needed between each genuine row in
        # the Elasticsearch import file

        with fileinput.FileInput(self.commodities_filename1, inplace=True, backup='.bak') as f:
            for line in f:
                text_to_search = "\n"
                replacement_text = '\n{ "index": {} }\n'
                print(line.replace(text_to_search, replacement_text), end='')
        f.close()
        # Open up the same file, this time for writing to
        with open(self.commodities_filename1, 'a') as f:
            f.write("\n")
        # Close the export file
        f.close()

        with fileinput.FileInput(self.commodities_filename2, inplace=True, backup='.bak') as f:
            for line in f:
                text_to_search = "\n"
                replacement_text = '\n{ "index": {} }\n'
                print(line.replace(text_to_search, replacement_text), end='')
        f.close()
        # Open up the same file, this time for writing to
        with open(self.commodities_filename2, 'a') as f:
            f.write("\n")
        # Close the export file
        f.close()

        # Delete the backups
        os.remove(self.commodities_filename1 + ".bak")
        os.remove(self.commodities_filename2 + ".bak")

    def complete(self):
        print("Generation of commodities.ndjson complete")
