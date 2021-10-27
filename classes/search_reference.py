import classes.globals as g


class SearchReference(object):
    def __init__(self, item):
        self.title = item["attributes"]["title"]
        self.referenced_id = item["attributes"]["referenced_id"].ljust(10, "0")
        self.referenced_class = item["attributes"]["referenced_class"]
