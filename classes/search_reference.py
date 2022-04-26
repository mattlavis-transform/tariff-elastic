import classes.globals as g


class SearchReference(object):
    def __init__(self, item):
        self.title = item["attributes"]["title"]
        self.goods_nomenclature_item_id = item["attributes"]["referenced_id"].ljust(10, "0")
        self.referenced_class = item["attributes"]["referenced_class"]
        self.productline_suffix = "80"
        self.promoted_description = item["attributes"]["title"]
        self.sid = None
        self.set_json()

    def set_json(self):
        self.json = {}
        # self.json["id"] = "ref_" + self.goods_nomenclature_item_id + self.productline_suffix
        self.json["sid"] = self.sid
        self.json["goods_nomenclature_item_id"] = self.goods_nomenclature_item_id
        self.json["productline_suffix"] = self.productline_suffix
        self.json["class"] = self.referenced_class
        self.json["description"] = self.promoted_description
        self.json["promoted_description"] = self.promoted_description
