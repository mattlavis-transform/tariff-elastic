import os
import fileinput
import csv
import json
import ndjson
import requests
from dotenv import load_dotenv
from classes.classification import Classification
from classes.search_reference import SearchReference
from classes.synonym import Synonym
import classes.globals as g


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
        self.commodities_filename = os.path.join("resources", "ndjson", "commodities.ndjson")
        self.metadata_folder = os.path.join(os.getcwd(), "resources", "meta")

        self.load_synonyms()
        self.load_stopwords()
        self.get_search_references()
        self.get_friendly_names()
        self.get_facet_assignments()
        self.get_metadata()

        self.load_commodity_code_data()
        self.inherit_assignments()
        self.apply_assignments_to_commodities()
        self.get_hierarchy_node()
        self.get_others_staged()
        # self.get_others()
        self.process_data()
        self.write_data()
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
        g.stopwords = self.stopwords
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
        self.write_search_references()
        print("- Complete\n")

    def write_search_references(self):
        filename = os.path.join(os.getcwd(), "resources", "search_references.csv")
        f = open(filename, 'w')
        writer = csv.writer(f)
        for search_reference in self.search_references:
            row = [search_reference.goods_nomenclature_item_id, search_reference.referenced_class, search_reference.title]
            a = 1
            writer.writerow(row)
        f.close()

    def apply_assignments_to_commodities(self):
        print("Getting assigning facet assignments to commodities")
        for c in self.classifications:
            c.get_facet_assignments()
        print("- Complete\n")

    def get_friendly_names(self):
        print("Getting friendly commodity code descriptions")
        with open(self.friendly_descriptions_file) as f:
            friendly_descriptions_data = ndjson.load(f)
            g.friendly_names = {}
            for item in friendly_descriptions_data:
                g.friendly_names[item["heading"].ljust(10, "0")] = g.cleanse_friendly_name(item["description"])

        print("- Complete\n")

    def get_facet_assignments(self):
        print("Getting facet assignments")
        with open(self.facets_export_file) as f:
            facet_assignments = ndjson.load(f)
            g.facet_assignments = {}
            for item in facet_assignments:
                sid = item["goods_nomenclature_sid"]
                if sid in g.facet_assignments:
                    g.facet_assignments[sid].append(item)
                else:
                    g.facet_assignments[sid] = [item]
        print("- Complete\n")

    def inherit_assignments(self):
        print("Inheriting down facet assignments")
        for i in range(0, len(self.classifications)):
            c = self.classifications[i]
            if c.sid in g.facet_assignments:
                for j in range(i + 1, len(self.classifications)):
                    c2 = self.classifications[j]
                    if c2.indent <= c.indent:
                        break
                    else:
                        if c2.sid not in g.facet_assignments:
                            g.facet_assignments[c2.sid] = g.facet_assignments[c.sid]
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
        print("Loading commodity code data")
        self.classifications = []
        self.classification_dict = {}
        with open(self.commodity_file) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            for row in csv_reader:
                if line_count > 0:
                    classification = Classification(row)
                    self.classifications.append(classification)
                    self.classification_dict[classification.goods_nomenclature_item_id_plus_pls] = classification
                line_count += 1
        print(
            f'- Complete: processes {line_count} lines of the goods classification.\n')

    def get_hierarchy_node(self):
        for classification in self.classifications:
            classification.hierarchy_json = []
            if len(classification.hierarchy_dict) > 0:
                for hierarchy_tier in classification.hierarchy_dict:
                    classification.hierarchy_dict[hierarchy_tier].description = self.classification_dict[hierarchy_tier].description
                    classification.hierarchy_dict[hierarchy_tier].classification_class = self.classification_dict[hierarchy_tier].classification_class
                    item = {
                        "goods_nomenclature_item_id": classification.hierarchy_dict[hierarchy_tier].goods_nomenclature_item_id,
                        "productline_suffix": classification.hierarchy_dict[hierarchy_tier].productline_suffix,
                        "class": classification.hierarchy_dict[hierarchy_tier].classification_class,
                        "description": classification.hierarchy_dict[hierarchy_tier].description
                    }
                    classification.hierarchy_json.append(item)
                    classification.hierarchy.append(
                        classification.hierarchy_dict[hierarchy_tier].description)

    def get_others(self):
        for classification in self.classifications:
            classification.siblings.reverse()
            if "other" in classification.description.lower().strip() == "other":
                sibling_count = len(classification.siblings)
                if sibling_count == 1:
                    if "less than" in classification.siblings[0].lower():
                        classification.description_alternative = classification.siblings[0].replace(
                            "less than ", "") + " or more"
                    elif " or " in classification.siblings[0].lower():
                        classification.description_alternative = "Neither " + \
                            g.decapitalize(
                                classification.siblings[0].replace(" or ", " nor "))
                    else:
                        classification.description_alternative = "Not " + \
                            g.decapitalize(classification.siblings[0])
                elif sibling_count == 2:
                    classification.description_alternative = "Neither "
                    sibling_index = 0
                    for sib in classification.siblings:
                        sibling_index += 1
                        if sibling_index > 1:
                            if sibling_index == sibling_count:
                                classification.description_alternative += " nor "
                            else:
                                classification.description_alternative += ", "
                        classification.description_alternative += g.decapitalize(
                            sib)
                else:
                    classification.description_alternative = "Not "
                    sibling_index = 0
                    for sib in classification.siblings:
                        sibling_index += 1
                        if sibling_index > 1:
                            if sibling_index == sibling_count:
                                classification.description_alternative += " or "
                            else:
                                classification.description_alternative += ", "
                        classification.description_alternative += g.decapitalize(
                            sib)

    def get_others_staged(self):
        for classification in self.classifications:
            classification.description_alternative = classification.description
        return
        # Do this, looping through the hierarchy 1 by 1, starting at indent of subheadings
        # (there are no others higher than that)
        for indent in range(1, 13):
            for classification in self.classifications:
                if classification.indent == indent:
                    # if "other" in classification.description.lower().strip(): # == "other":
                    if classification.description.lower().strip() == "other":
                        # Check for live horses, asses, mules and hinnies
                        ret = classification.check_parent_of_other()
                        if ret != "":
                            classification.description_alternative = ret
                        else:
                            classification.siblings.reverse()
                            sibling_count = len(classification.siblings)
                            if sibling_count == 1:
                                if "less than" in classification.siblings[0].lower():
                                    classification.description_alternative = classification.siblings[0].replace(
                                        "less than ", "") + " or more"
                                elif " or " in classification.siblings[0].lower():
                                    classification.description_alternative = "Neither " + \
                                        g.decapitalize(
                                            classification.siblings[0].replace(" or ", " nor "))
                                else:
                                    classification.description_alternative = "Not " + \
                                        g.decapitalize(
                                            classification.siblings[0])
                            elif sibling_count == 2:
                                classification.description_alternative = "Neither "
                                sibling_index = 0
                                for sib in classification.siblings:
                                    sibling_index += 1
                                    if sibling_index > 1:
                                        if sibling_index == sibling_count:
                                            classification.description_alternative += " nor "
                                        else:
                                            classification.description_alternative += ", "
                                    classification.description_alternative += g.decapitalize(
                                        sib)
                            else:
                                classification.description_alternative = "Not "
                                sibling_index = 0
                                for sib in classification.siblings:
                                    sibling_index += 1
                                    if sibling_index > 1:
                                        if sibling_index == sibling_count:
                                            classification.description_alternative += " or "
                                        else:
                                            classification.description_alternative += ", "
                                    classification.description_alternative += g.decapitalize(
                                        sib)

    def process_data(self):
        for classification in self.classifications:
            classification.get_terms(self.stopwords, self.synonyms_dict)
            classification.get_search_references(self.search_references_dict)

    def write_data(self):
        ndjson_list = []
        ndjson_list2 = []
        for classification in self.classifications:
            classification.get_chapter_heading()
            classification.write(self.dest_folder)
            ndjson_list.append(classification.json)

        for search_reference in self.search_references:
            ndjson_list2.append(search_reference.json)

        file_exists = os.path.exists(self.commodities_filename)
        if file_exists:
            os.remove(self.commodities_filename)

        with open(self.commodities_filename, 'w') as f:
            f.write('\n')
            ndjson.dump(ndjson_list, f)
            if self.include_search_refs == 1:
                f.write("\n")
                ndjson.dump(ndjson_list2, f)

    def insert_blank_index_lines(self):
        # The line { "index": {} } is needed between each genuine row in
        # the Elasticsearch import file
        with fileinput.FileInput(self.commodities_filename, inplace=True, backup='.bak') as f:
            for line in f:
                text_to_search = "\n"
                replacement_text = '\n{ "index": {} }\n'
                print(line.replace(text_to_search, replacement_text), end='')
        f.close()
        # Open up the same file, this time for writing to
        with open(self.commodities_filename, 'a') as f:
            f.write("\n")
        # Close the export file
        f.close()

    def get_metadata(self):
        a = 1

    def complete(self):
        print("Generation of commodities.ndjson complete")
