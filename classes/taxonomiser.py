import os
import json
import ndjson
import openpyxl
import csv
from dotenv import load_dotenv
from openpyxl.cell import cell

from classes.commodity import Commodity
from classes.heading import Heading
from classes.facet import Facet


class Taxonomiser:
    def __init__(self):
        load_dotenv('.env')
        self.commodity_file = os.getenv('COMMODITY_MASTER')
        self.database_url = os.getenv('DATABASE_UK')
        self.facet_source_file = os.getenv('FACETS_MASTER')
        self.facet_source_file = os.path.join(os.getcwd(), "resources", "facets_source", self.facet_source_file)

        self.es_settings_template_path = os.getenv('ES_SETTINGS_TEMPLATE_PATH')
        self.es_settings_path = os.getenv('ES_SETTINGS_PATH')
        self.js_filter_path = os.getenv('JS_FILTER_PATH')

        self.commodities = []
        self.facets = {}
        self.headings = []
        self.headings_dict = {}
        self.facets_export_folder = os.path.join(os.getcwd(), "resources", "facets_export")

    def get_facets(self):
        # Get the facets from the source Excel spreadsheet
        wb_obj = openpyxl.load_workbook(self.facet_source_file)
        sheet_facets = wb_obj["facets"]
        max_row = sheet_facets.max_row
        max_col = sheet_facets.max_column

        self.facets = []
        self.facets_dict = {}
        for i in range(2, max_row + 1):
            item = {
                "field": sheet_facets.cell(row=i, column=1).value,
                "display_name": sheet_facets.cell(row=i, column=2).value
            }
            self.facets.append(item)
            self.facets_dict[sheet_facets.cell(row=i, column=1).value] = sheet_facets.cell(row=i, column=2).value

        self.write_elasticsearch_template()

        # Get the headings
        sheet_headings = wb_obj["headings"]
        max_row = sheet_headings.max_row
        max_col = sheet_headings.max_column

        for i in range(2, max_row):
            h = Heading()
            h.id = sheet_headings.cell(row=i, column=1).value
            for j in range(3, max_col):
                v = sheet_headings.cell(row=i, column=j).value
                if v != "" and v is not None:
                    h.add_facet(v)

            self.headings.append(h)
            self.headings_dict[h.id] = h.facets
        wb_obj = None

    def write_elasticsearch_template(self):
        # Read in the template
        f = open(self.es_settings_template_path, "r")
        data = json.load(f)
        f.close()
        mappings = data["mappings"]
        properties = mappings["properties"]

        js_filter_data = {}
        for facet in self.facets_dict:
            new_key = "filter_" + facet
            data["mappings"]["properties"][new_key] = {
                "type": "text",
                "fields": {
                        "raw": {
                            "type": "keyword"
                        }
                }
            }
            js_filter_data[facet] = {
                "display": self.facets_dict[facet],
                "level": "results"
            }

        # Write out the master file with the facets included
        json_object = json.dumps(data, indent=4)
        with open(self.es_settings_path, "w") as outfile:
            outfile.write(json_object)
        outfile.close()

        # Write out the JS filter path
        json_object = json.dumps(js_filter_data, indent=4)
        with open(self.js_filter_path, "w") as outfile:
            outfile.write(json_object)
        outfile.close()
        a = 1

    def get_commodities(self):
        # Loops through the list of commodities extracted from the "download Taric files > codes.py"
        # service: this list is then used to act as the base for adding filters to the extracted
        # data JSON file
        with open(self.commodity_file) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            for row in csv_reader:
                if line_count == 0:
                    line_count += 1
                else:
                    c = Commodity(row)
                    self.commodities.append(c)
                    line_count += 1

    def get_key_terms(self):
        for c in self.commodities:
            if c.number_indents > 0:
                if c.heading in self.headings_dict:
                    c.expand_facets(self.headings_dict[c.heading])

    def apply_commodity_hierarchy(self):
        # In which the hierarchy of the classification in formed by
        # looping from the end to the start and finding each decrement
        # of the number of indents

        # This code also inherits
        for i in range(len(self.commodities) - 1, -1, -1):
            c = self.commodities[i]
            indent_rolling = c.number_indents
            for j in range(i - 1, -1, -1):
                c2 = self.commodities[j]
                if c2.number_indents < indent_rolling:
                    c.hierarchy.append(c2)
                    indent_rolling = c2.number_indents
                if c2.number_indents == 0:
                    break

        for c in self.commodities:
            c.inherit_facets()

    def save(self):
        # Write a test JSON to validate that the assignment of key terms is working
        self.json = {}
        self.filters = []
        for c in self.commodities:
            self.json[c.goods_nomenclature_item_id] = c.facets
            for facet in c.facets:
                if len(c.facets[facet]) > 0:
                    assignment = {}
                    assignment["goods_nomenclature_sid"] = c.sid
                    assignment["goods_nomenclature_item_id"] = c.goods_nomenclature_item_id
                    assignment["productline_suffix"] = c.productline_suffix
                    assignment["filter_name"] = "filter_" + facet
                    assignment["value"] = c.facets[facet]

                    self.filters.append(assignment)

        # Write JSON file
        # json_file = os.path.join(self.facets_export_folder, "data.json")
        # with open(json_file, 'w') as outfile:
        #     json.dump(self.json, outfile, indent=4)

        # Write NDJSON file
        # This is used in emulate
        ndjson_file = os.path.join(self.facets_export_folder, os.getenv("FACETS_FILE"))
        with open(ndjson_file, 'w') as f:
            ndjson.dump(self.filters, f)
