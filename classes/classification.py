import os
import json
import string
from datetime import datetime
from dotenv import load_dotenv
import classes.globals as g


class Classification(object):
    def __init__(self, row):
        self.row = row
        self.sid = int(row[0])
        self.goods_nomenclature_item_id = row[1]
        self.productline_suffix = row[2]
        self.validity_start_date = self.date_format(row[3])
        self.validity_end_date = self.date_format(row[4])
        self.indent = int(row[5])
        self.end_line = int(row[6])
        self.description = row[7]
        self.description_alternative = ""
        self.classification_class = ""
        self.hierarchy = []
        self.full_hierarchy = []
        self.siblings = []
        self.terms = []
        self.excluded_terms = []
        self.terms_hierarchy = []
        self.search_references = []
        del self.row

        self.get_class()
        self.get_friendly()
        # self.get_assignments()
        self.format_description()

    def date_format(self, s):
        if s == "":
            s = None
            s = "2099-12-31"
        else:
            s = datetime.strptime(s, '%d/%m/%Y').strftime('%Y-%m-%d')
        return s
    
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
            if self.end_line:
                self.classification_class = "commodity"
            else:
                self.classification_class = "intermediate"

    def get_terms(self, stopwords, synonyms):
        self.stopwords = stopwords
        # Get the terms from the description
        if self.description_alternative == "":
            base = self.description
        else:
            base = self.description_alternative
            
        base = base.lower()
        
        exclusion_terms = [
            "other than",
            "excluding",
            "except"
        ]
        
        self.excluded = ""
        for exclusion_term in exclusion_terms:
            if exclusion_term in base:
                parts = base.split(exclusion_term)
                base = parts[0]
                self.description_alternative = base
                self.excluded = parts[1]
                self.write_exclusion_terms()

        parts = base.split()
        for part in parts:
            part = g.cleanse(part).lower()
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

    def write_exclusion_terms(self):
        parts = self.excluded.split()
        for part in parts:
            part = g.cleanse(part).lower()
            if part not in self.terms:
                if part not in self.stopwords:
                    self.excluded_terms.append(part)

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

    def get_full_hierarchy_json(self):
        self.hierarchy_json = []
        for hier in self.full_hierarchy:
            item = {
                "goods_nomenclature_item_id": hier.goods_nomenclature_item_id,
                "productline_suffix": hier.productline_suffix,
                "classification_class": hier.classification_class,
                "description": hier.description
            }
            self.hierarchy_json.append(item)
    
    def write(self, dest_folder):
        if self.description_alternative == "":
            self.description_alternative = self.description
        
        self.filename = os.path.join(dest_folder, self.goods_nomenclature_item_id + self.productline_suffix + ".json")

        self.json = {}
        self.json["sid"] = self.sid
        self.json["goods_nomenclature_item_id"] = self.goods_nomenclature_item_id
        self.json["heading_id"] = self.goods_nomenclature_item_id[0:4]
        self.json["chapter_id"] = self.goods_nomenclature_item_id[0:2]
        self.json["productline_suffix"] = self.productline_suffix
        self.json["class"] = self.classification_class
        self.json["description"] = self.description
        self.json["description_alternative"] = self.description_alternative
        self.json["chapter"] = self.chapter
        self.json["heading"] = self.heading
        self.json["hierarchy"] = self.hierarchy_json
        self.json["search_references"] = self.search_references
        self.json["validity_start_date"] = self.validity_start_date
        self.json["validity_end_date"] = self.validity_end_date
        
        # Add in the custom assignments if they exist
        for key, value in self.assignments.items():
            self.json[key] = value
        
        # Add in ancestry
        for i in range (0, 12):
            if len(self.hierarchy) > i:
                self.json["ancestor_" + str(i)] = self.hierarchy[i]
                
        if 0 > 1:
            self.json["terms"] = self.terms
            self.json["excluded_terms"] = self.excluded_terms
            self.json["terms_hierarchy"] = self.terms_hierarchy
            self.json["friendly_name"] = self.friendly_name

        with open(self.filename, 'w') as outfile:
            json.dump(self.json, outfile, indent=4)
            
    def check_parent_of_other(self):
        a = 1
        q = g.stopwords
        if "020860" in self.goods_nomenclature_item_id:
            a = 1
        parent = self.hierarchy[0].lower()
        exclude = set(string.punctuation)
        parent = ''.join(ch for ch in parent if ch not in exclude)
        parent_parts = parent.split()
        for element in parent_parts:
            if element in g.stopwords:
                parent_parts.remove(element)
        a = 1
        
        parent_modified = parent
        for sibling in self.siblings:
            tmp = sibling.lower()
            parent_modified = parent_modified.replace(tmp, "")

        if parent_modified != parent:
            parent_modified = parent_modified.replace(" ,", ",")
            parent_modified = parent_modified.replace(", , ", ", ")
            parent_modified = parent_modified.replace(",, ", ",")
            parent_modified = parent_modified.replace(",", " ")
            parent_modified = parent_modified.capitalize()
            if parent_modified.lower() != parent.lower():
                return parent_modified
            else:
                return ""
        else:
            return ""

