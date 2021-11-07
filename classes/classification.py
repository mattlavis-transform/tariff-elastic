import os
import json
from datetime import datetime
from dotenv import load_dotenv
import classes.globals as g


class Classification(object):
    def __init__(self, row):
        self.row = row
        self.sid = int(row[0])
        self.goods_nomenclature_item_id = row[1]
        self.productline_suffix = row[2]
        self.indent = int(row[5])
        self.end_line = int(row[6])
        self.description = row[7]
        self.description_alternative = ""
        self.classification_class = ""
        self.hierarchy = []
        self.siblings = []
        self.terms = []
        self.terms_hierarchy = []
        self.search_references = []
        del self.row

        self.get_class()
        self.get_friendly()
        # self.get_assignments()
        self.format_description()

    def format_description(self):
        self.description = self.description.replace("\u00a0", " ")
        
    def get_friendly(self):
        if self.goods_nomenclature_item_id in g.friendly_names:
            self.friendly_name = g.friendly_names[self.goods_nomenclature_item_id]
        else:
            self.friendly_name = ""
        
    def get_assignments(self):
        self.assignments = {}
        if self.sid in g.assignments:
            assignments = g.assignments[self.sid]
            for assignment in assignments:
                self.assignments[assignment["filter_name"]] = assignment["value"]


    def get_class(self):
        if g.right(self.goods_nomenclature_item_id, 8) == "00000000":
            self.classification_class = "chapter"
            self.description = self.description.capitalize()
        elif g.right(self.goods_nomenclature_item_id, 6) == "000000":
            self.classification_class = "heading"
        else:
            self.classification_class = "commodity"
            
        a = 1
    
    def get_terms(self, stopwords, synonyms):
        # Get the terms from the description
        if self.description_alternative == "":
            base = self.description
        else:
            base = self.description_alternative
            
        base = base.lower()
        if "other than" in base:
            parts = base.split("other than")
            base = parts[0]
            
        if "excluding" in base:
            parts = base.split("excluding")
            base = parts[0]
            
            
        parts = base.split()
        for part in parts:
            part = g.cleanse(part).lower()
            if self.goods_nomenclature_item_id == "0302210000":
                a = 1
            # Get the synonyms for part
            if part not in stopwords:
                if part in synonyms:
                    list_of_synonyms = synonyms[part]
                    list_of_synonyms.append(part)
                    for synonym in list_of_synonyms:
                        if synonym.lower() not in self.terms:
                            self.terms.append(synonym.lower())
                else:
                    if part.lower() not in self.terms:
                        self.terms.append(part.lower())
                
        # Get the terms from the hierarchy
        for item in self.hierarchy:
            if "other" not in item.lower():
                parts = item.split()
                for part in parts:
                    part = g.cleanse(part)
                    if part not in stopwords:
                        self.terms_hierarchy.append(part.lower())

    def get_search_references(self, search_references_dict):
        if self.goods_nomenclature_item_id in search_references_dict:
            self.search_references = search_references_dict[self.goods_nomenclature_item_id]
            a = 1
        else:
            b = 1
        a = 1
        
    def get_search_references_old(self, search_references):
        for search_reference in search_references:
            if search_reference.goods_nomenclature_item_id == self.goods_nomenclature_item_id:
                self.search_references.append(search_reference.title)

    def get_chapter_heading(self):
        if self.classification_class == "chapter":
            self.chapter = self.description
            self.heading = None
        elif self.classification_class == "heading":
            self.chapter = self.hierarchy[0]
            self.heading = self.description
        else:
            self.chapter = self.hierarchy[-1]
            self.heading = self.hierarchy[-2]

    def write(self, dest_folder):
        self.filename = os.path.join(dest_folder, self.goods_nomenclature_item_id + self.productline_suffix + ".json")
        self.json = {}
        # self.json["id"] = self.goods_nomenclature_item_id + self.productline_suffix
        self.json["sid"] = self.sid
        self.json["goods_nomenclature_item_id"] = self.goods_nomenclature_item_id
        self.json["productline_suffix"] = self.productline_suffix
        self.json["class"] = self.classification_class
        self.json["description"] = self.description
        self.json["description_alternative"] = self.description_alternative
        self.json["chapter"] = self.chapter
        self.json["heading"] = self.heading
        self.json["friendly_name"] = self.friendly_name
        
        # Add in the custom assignments if they exist
        for key, value in self.assignments.items():
            self.json[key] = value
        
        # Add in ancestry
        for i in range (0, 12):
            if len(self.hierarchy) > i:
                self.json["ancestor_" + str(i)] = self.hierarchy[i]
                
        if 1 > 2:
            self.json["search_references"] = self.search_references
            self.json["terms"] = self.terms
            self.json["terms_hierarchy"] = self.terms_hierarchy

        with open(self.filename, 'w') as outfile:
            json.dump(self.json, outfile, indent=4)
            
        a = 1