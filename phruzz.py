import spacy
import classy_classification

data = {
    "furniture": ["This text is about chairs.",
                  "Couches, benches and televisions.",
                  "I really need to get a new sofa."],
    "kitchen": ["There also exist things like fridges.",
                "I hope to be getting a new stove today.",
                "Do you also have some ovens."]
}

nlp = spacy.load("en_core_web_md")
nlp.add_pipe(
    "text_categorizer",
    config={
        "data": data,
        "model": "spacy"
    }
)

print(nlp("I am looking for kitchen appliances.")._.cats)
