class Facet:
    def __init__(self):
        self.field_name = None
        self.display_name = None
        self.values = []

    def add_value(self, v):
        self.values.append(v)

    def get_display_name(self):
        pass
