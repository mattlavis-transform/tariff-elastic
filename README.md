# Create tariff data corpus for Elasticsearch

## Implementation steps

- Create and activate a virtual environment, e.g.

  `python3 -m venv venv/`
  `source venv/bin/activate`

- Install necessary Python modules via `pip3 install -r requirements.txt`

- Save necessary Python modules via `pip3 freeze > requirements.txt`

## Usage

### Create the facets for use in the Elasticsearch data file
`python3 create_facets.py`

#### How does the create filters function work

- The master data set is stored in the Excel spreadsheet referenced in the FACETS_MASTER environment variable
- This data file

### To create the NDJSON data
`python3 generate_es_corpus.py`


### To import data into Elasticsearch
`./es_import`

