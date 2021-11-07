import os
import sys
import fileinput
import csv
import json
import ndjson
import requests
from datetime import datetime
from dotenv import load_dotenv
from classes.classification import Classification
from classes.search_reference import SearchReference
from classes.manual_categorisation import ManualCategorisation
from classes.synonym import Synonym
import classes.globals as g

class Application(object):
    def __init__(self):
        load_dotenv('.env')
        self.include_search_refs = int(os.getenv('INCLUDE_SEARCH_REFS'))
        self.source_file = os.path.join(os.getcwd(), "resources", os.getenv('SOURCE_FILE'))
        self.dest_folder = os.path.join(os.getcwd(), "resources", "json")
        self.stopwords_file = os.path.join(os.getcwd(), "resources", os.getenv('STOPWORDS_FILE'))
        self.synonyms_file = os.path.join(os.getcwd(), "resources", os.getenv('SYNONYMS_FILE'))
        self.commodities_filename = os.path.join("resources", "ndjson", "commodities.ndjson")
        
        self.load_manual_categorisation()
        self.load_synonyms()
        self.get_search_references()
        self.get_friendly_names()
        self.get_assignments()
        
        self.load_stopwords()
        self.load_data()
        self.inherit_assignments()
        self.assign_assignments_to_commodities()
        self.get_hierarchy_and_siblings()
        self.get_others()
        self.process_data()
        self.write_data()
        self.post_process()
        self.complete()
        
    def assign_assignments_to_commodities(self):
        for c in self.classifications:
            c.get_assignments()
        
    def get_friendly_names(self):
        with open('/Users/mattlavis/sites and projects/1. Online Tariff/scrape-tariff-number/tns.ndjson') as f:
            tns_data = ndjson.load(f)
            g.friendly_names = {}
            for item in tns_data:
                g.friendly_names[item["heading"].ljust(10, "0")] = item["description"]

    def get_assignments(self):
        with open('assignments.ndjson') as f:
            assignments = ndjson.load(f)
            g.assignments = {}
            for item in assignments:
                sid = item["goods_nomenclature_sid"]
                if sid in g.assignments:
                    g.assignments[sid].append(item)
                else:
                    g.assignments[sid] = [item]

    def inherit_assignments(self):
        for i in range(0, len(self.classifications)):
            c = self.classifications[i]
            sid = c.sid
            if sid in g.assignments:
                a = 1
                for j in range(i + 1, len(self.classifications)):
                    c2 = self.classifications[j]
                    if c2.indent <= c.indent:
                        break
                    else:
                        if c2.sid not in g.assignments:
                            g.assignments[c2.sid] = g.assignments[c.sid]
                    pass
        a = 1

    def load_manual_categorisation(self):
        self.manual_categorisation = ManualCategorisation()
        
    def get_search_references(self):
        self.search_references = []
        self.search_references_dict = {}
        alphabet = "abcdefghijklmnopqrstuvwxyz"
        # alphabet = "x"
        for i in range(0, len(alphabet)):
            letter = alphabet[i:i+1]
            url = "https://www.trade-tariff.service.gov.uk/api/v2/search_references.json?query[letter]=" + letter
            response = requests.get(url)
            data = response.json()["data"]
            for item in data:
                search_reference = SearchReference(item)
                self.search_references.append(search_reference)
                if search_reference.goods_nomenclature_item_id in self.search_references_dict:
                    self.search_references_dict[search_reference.goods_nomenclature_item_id].append(search_reference.title)
                else:
                    self.search_references_dict[search_reference.goods_nomenclature_item_id] = [search_reference.title]
            print("Deriving curated terms beginning with", letter)
        # Sort the search references
        self.search_references = sorted(self.search_references, key=lambda x: int(x.goods_nomenclature_item_id))
        # self.search_references_dict = sorted(self.search_references_dict)
        a = 1

    def load_stopwords(self):
        f = open(self.stopwords_file)
        self.stopwords = json.load(f)
        f.close()
        
    def load_synonyms(self):
        f = open(self.synonyms_file)
        self.synonyms_json = json.load(f)["data"]["synonyms"]
        f.close()
        self.parse_synonyms()
        
    def parse_synonyms(self):
        self.synonyms = []
        for synonym_raw in self.synonyms_json:
            synonym = Synonym(synonym_raw)
            self.synonyms.append(synonym)
        self.create_synonym_dictionary()

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
                                
        # with open('file.txt', 'w') as file:
        #     file.write(json.dumps(self.synonyms_dict, indent=4))

    def load_data(self):
        self.classifications = []
        with open(self.source_file) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            for row in csv_reader:
                if line_count > 0:
                    classification = Classification(row)
                    self.classifications.append(classification)
                line_count += 1
            print(f'Processed {line_count} lines of the goods classification.')

    def get_hierarchy_and_siblings(self):
        starting_point = "2300000000"
        starting_point = "9999999999"

        for i in range(len(self.classifications) - 1, -1, -1):
            classification = self.classifications[i]
            can_find_siblings = True
            if classification.goods_nomenclature_item_id < starting_point:
                indent = classification.indent
                for j in range(i - 1, -1, -1):
                    antecedent = self.classifications[j]
                    if antecedent.indent < indent or antecedent.classification_class == "chapter":
                        indent = antecedent.indent
                        classification.hierarchy.append(g.cleanse(antecedent.description))
                        can_find_siblings = False

                    if can_find_siblings:
                        if antecedent.indent == indent:
                            antecedent.siblings.append(classification.description)
                            classification.siblings.append(g.cleanse(antecedent.description))

                    if antecedent.indent == 0 and antecedent.classification_class == "chapter":
                        break

    def get_others(self):
        for classification in self.classifications:
            classification.siblings.reverse()
            if "other" in classification.description.lower().strip() == "other":
                sibling_count = len(classification.siblings)
                if sibling_count == 1:
                    if "less than" in classification.siblings[0].lower():
                        classification.description_alternative = classification.siblings[0].replace("less than ", "") + " or more"
                    elif " or " in classification.siblings[0].lower():
                        classification.description_alternative = "Neither " + g.decapitalize(classification.siblings[0].replace(" or ", " nor "))
                    else:
                        classification.description_alternative = "Not " + g.decapitalize(classification.siblings[0])
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
                        classification.description_alternative += g.decapitalize(sib)
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
                        classification.description_alternative += g.decapitalize(sib)
                a = 1

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
                
        try:
            os.remove(self.commodities_filename)
        except:
            pass
        
        with open(self.commodities_filename, 'w') as f:
            f.write('\n')
            ndjson.dump(ndjson_list, f)
            if self.include_search_refs == 1:
                f.write("\n")
                ndjson.dump(ndjson_list2, f)

    def post_process(self):
        filename = self.commodities_filename
        with fileinput.FileInput(filename, inplace=True, backup='.bak') as f:
            # print( '{ "index": {} }\n')
            for line in f:
                text_to_search = "\n"
                replacement_text = '\n{ "index": {} }\n'
                print(line.replace(text_to_search, replacement_text), end='')
                
        f.close()
        
        with open(self.commodities_filename, 'a') as f:
            f.write("\n")
        f.close()
        


    def complete(self):
        print("Generation of commodities.ndjson complete")