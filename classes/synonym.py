import classes.globals as g


class Synonym(object):
    def __init__(self, synonym_raw):
        self.raw = synonym_raw
        self.terms_from = []
        self.terms_to = []
        self.terms = []
        if "=>" in synonym_raw:
            self.bi_directional = False
            parts = self.raw.split("=>")
            self.parts_from = parts[0]
            self.parts_to = parts[1]

        else:
            self.bi_directional = True
            parts = self.raw.split(",")
            for part in parts:
                self.terms.append(part.strip())
                
        # "i-pod, i pod => ipod",
        # "universe, cosmos"
        del self.raw
