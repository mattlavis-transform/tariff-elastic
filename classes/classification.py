import os
import json
import string
import classes.globals as g


class Classification(object):
    def __init__(self, row=None):
        self.sid = None
        self.goods_nomenclature_item_id = ""
        self.productline_suffix = ""
        self.validity_start_date = ""
        self.validity_end_date = ""
        self.indent = None
        self.end_line = None
        self.description = ""
        self.classification_class = ""
        self.goods_nomenclature_item_id_plus_pls = ""
        self.hierarchy_string = ""
        self.parent_sid = None
        self.friendly_name = ""

        self.description_alternative = ""
        self.hierarchy = []
        self.full_hierarchy = []
        self.siblings = []
        self.terms = []
        self.excluded_terms = []
        self.terms_hierarchy = []
        self.search_references = []

        if row is not None:
            self.row = row
            self.sid = int(row[0])
            self.goods_nomenclature_item_id = row[1]
            self.productline_suffix = row[2]
            self.comm_code_plus_pls = self.goods_nomenclature_item_id + "_" + self.productline_suffix
            self.validity_start_date = g.date_format(row[3])
            self.validity_end_date = g.date_format(row[4])
            self.indent = int(row[5])
            self.end_line = int(row[6])
            self.classification_class = row[8]
            self.description = g.cleanse(row[7], self.classification_class)
            self.goods_nomenclature_item_id_plus_pls = row[9]
            self.hierarchy_string = row[10]
            self.parent_comm_code_plus_pls = None

            del self.row

            self.get_friendly()
            self.expand_hierarchy_string()

    def expand_hierarchy_string(self):
        self.hierarchy_dict = {}
        if self.hierarchy_string != "":
            parts = self.hierarchy_string.split(",")
            for part in parts:
                string_parts = part.split("_")
                c = Classification()
                c.goods_nomenclature_item_id = string_parts[0]
                c.productline_suffix = string_parts[1]
                c.goods_nomenclature_item_id_plus_pls = part
                self.hierarchy_dict[part] = c

    def get_friendly(self):
        if self.productline_suffix == "80":
            if self.goods_nomenclature_item_id in g.friendly_names:
                self.friendly_name = g.friendly_names[self.goods_nomenclature_item_id]

    def get_facet_assignments(self):
        self.assignments = {}
        if self.sid in g.facet_assignments:
            assignments = g.facet_assignments[self.sid]
            for assignment in assignments:
                self.assignments[assignment["filter_name"]] = assignment["value"]

    def get_terms(self, stopwords, synonyms):
        return
        self.stopwords = stopwords
        # Get the terms from the description
        if self.description_alternative == "":
            base = self.description
        else:
            base = self.description_alternative

        base = base.lower()

        exclusion_terms = [
            "neither",
            "other than",
            "excluding",
            "not including",
            "except",
            " not "
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
        return
        parts = self.excluded.split()
        for part in parts:
            part = g.cleanse(part).lower()
            if part not in self.terms:
                if part not in self.stopwords:
                    self.excluded_terms.append(part)

    def get_search_references(self, search_references_dict):
        if self.goods_nomenclature_item_id in search_references_dict:
            self.search_references = search_references_dict[self.goods_nomenclature_item_id]

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
                "class": hier.classification_class,
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
        self.json["friendly_name"] = self.friendly_name
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
        for i in range(0, 12):
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
        parent = self.hierarchy[0].lower()
        exclude = set(string.punctuation)
        parent = ''.join(ch for ch in parent if ch not in exclude)
        parent_parts = parent.split()
        for element in parent_parts:
            if element in g.stopwords:
                parent_parts.remove(element)

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
