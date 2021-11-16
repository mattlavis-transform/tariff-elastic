import os
from classes.database import Database
from dotenv import load_dotenv
import classes.globals as g


class WordNet(object):
    def __init__(self):
        pass
    
    def clear(self):
        self.clear_synsets()
        self.clear_terms()
        
    def clear_synsets(self):
        d = Database()
        sql = "DELETE FROM wordnet.synsets"
        d.run_query(sql)
        
    def clear_terms(self):
        d = Database()
        sql = "DELETE FROM wordnet.terms"
        d.run_query(sql)

class WordnetLine(object):
    def __init__(self, wordnet, raw):
        load_dotenv('.env')
        self.save_to_db_concurrent = int(os.getenv('SAVE_TO_DB_CONCURRENT'))
        self.wordnet = wordnet

        a = g.pointer_symbols
        self.raw = raw
        self.wordnet_words = []
        self.wordnet_relations = []
        self.valid = False
        self.description = ""
        
        self.parse()
        self.parse_description()
        self.form_json()
        self.save()

    def parse(self):
        self.parts = self.raw.split(" ")
        self.synset_offset = self.parts[0]       # essentially the unique ID
        self.lex_filenum = self.parts[1]         # the lexicographer's filename (https://wordnet.princeton.edu/documentation/lexnames5wn) - may be elpful in determining animal, vegetable, mineral etc.
        self.ss_type = self.parts[2]             # the synset type (we are only interested in nouns (n))
        self.word_count = int(self.parts[3], 16) # the number of words in the synset (stored in hex)
        
        self.lexicographer_file = g.lexicographer_files[self.lex_filenum]
        if self.lexicographer_file["permitted"] == "Y":
            self.valid = True

        if self.valid:
            # Get the words that make up this synset
            self.parts[0:4] = []
            self.raw = " ".join(self.parts)
            self.parts = self.raw.split(" ")

            for i in range(0, self.word_count):
                self.wordnet_words.append(WordnetTerm(self.synset_offset, self.parts[i * 2], self.parts[(i * 2) + 1]).json)

            self.parts[0:self.word_count * 2] = []
            self.raw = " ".join(self.parts)

            # Get the description
            offset = self.raw.find("|")
            self.description = self.raw[offset+2:]

            # Now get the relationships with other synsets
            self.raw = self.raw[:offset].strip()
            self.parts = self.raw.split(" ")
            self.pointer_cnt = int(self.parts[0])
            self.parts[0:1] = []
            for i in range(0, self.pointer_cnt):
                pointer_symbol = self.parts[i * 2]
                if pointer_symbol in g.pointer_symbols:
                    self.wordnet_relations.append(WordnetRelation(
                        self.synset_offset,
                        self.parts[i * 2],
                        self.parts[(i * 2) + 1],
                        self.parts[(i * 2) + 2],
                        self.parts[(i * 2) + 3]
                    ).json)
            
    def parse_description(self):
        if self.valid:
            self.description = self.description.replace("\n", "")
            self.description = self.description.strip()
            
    def form_json(self):
        if self.valid:
            self.json = {}
            self.json["synset_offset"] = self.synset_offset
            self.json["lex_filenum"] = self.lex_filenum
            self.json["lexicographer_file"] = self.lexicographer_file["name"]
            self.json["ss_type"] = self.ss_type
            self.json["word_count"] = self.word_count
            self.json["description"] = self.description
            self.json["terms"] = self.wordnet_words
            self.json["relations"] = self.wordnet_relations
            
            self.save_to_csv()
            
    def save_to_csv(self):
        g.f_wordnet_synset_file.write(self.synset_offset + ",")
        g.f_wordnet_synset_file.write(self.lex_filenum + ",")
        g.f_wordnet_synset_file.write(self.ss_type + ",")
        g.f_wordnet_synset_file.write(str(self.word_count) + ",")
        g.f_wordnet_synset_file.write('"' + self.description.replace('"', "'") + '"')
        g.f_wordnet_synset_file.write("\n")
    
    def save(self):
        if self.save_to_db_concurrent:
            d = Database()
            sql = """
            INSERT INTO wordnet.synsets
            (synset_offset, lex_filenum, ss_type, word_count, description)
            VALUES
            (%s, %s, %s, %s, %s)
            """
            params = [
                self.synset_offset,
                self.lex_filenum,
                self.ss_type,
                self.word_count,
                self.description
            ]
            d.run_query(sql, params)


class WordnetTerm(object):
    def __init__(self, synset_offset, term, term_index):
        self.json = {}
        term = term.replace("_", " ").lower()
        self.json["term"] = term
        self.json["term_index"] = term_index
        
        d = Database()
        sql = """
        INSERT INTO wordnet.terms
        (synset_offset, term, term_index)
        VALUES
        (%s, %s, %s)
        """
        params = [
            synset_offset,
            term,
            term_index
        ]
        d.run_query(sql, params)


class WordnetRelation(object):
    def __init__(self, synset_offset, pointer_symbol, relation_synset_offset, pos, source_target):
        self.json = {}
        self.json["pointer_symbol"] = pointer_symbol
        try:
            self.json["pointer_type"] = g.pointer_symbols[pointer_symbol]
        except:
            self.json["pointer_type"] = None
        self.json["relation_synset_offset"] = relation_synset_offset
        self.json["pos"] = pos
        self.json["source_target"] = source_target


        d = Database()
        sql = """
        INSERT INTO wordnet.relations
        (synset_offset, pointer_symbol, relation_synset_offset, pos, source_target)
        VALUES
        (%s, %s, %s, %s, %s)
        """
        params = [
            synset_offset,
            pointer_symbol,
            relation_synset_offset,
            pos,
            source_target
        ]
        d.run_query(sql, params)
