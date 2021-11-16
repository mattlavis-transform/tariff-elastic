-- Start by creating a search configuration
CREATE TEXT SEARCH CONFIGURATION tariffs ( COPY = pg_catalog.english );


-- Now create a synonym
-- By default, it goes here
-- /Applications/Postgres.app/Contents/Versions/12/share/postgresql/tsearch_data
CREATE TEXT SEARCH DICTIONARY tariffs (
    TEMPLATE = synonym,
    SYNONYMS = tariffs
);


-- Register the English spelling dictionary
CREATE TEXT SEARCH DICTIONARY english_ispell_tariffs (
    TEMPLATE = ispell,
    DictFile = en_us,
    AffFile = en_us,
    StopWords = english
);

-- Alter the mapping configuration
ALTER TEXT SEARCH CONFIGURATION pg
ALTER MAPPING FOR asciiword, asciihword, hword_asciipart,
word, hword, hword_part
WITH pg_dict, english_ispell, english_stem;

-- Drop incompatible types
ALTER TEXT SEARCH CONFIGURATION pg
DROP MAPPING FOR email, url, url_path, sfloat, float;

-- Test
SELECT * FROM ts_debug('public.pg', 'penis, 
PostgreSQL, the highly scalable, SQL compliant, open source object-relational
database management system, is now undergoing beta testing of the next
version of our software.
');

-- Set the default search config 
SET default_text_search_config = 'public.pg';

SHOW default_text_search_config;

/* =====================
 
		version 2

======================== */


CREATE TEXT SEARCH DICTIONARY syn (template=synonym, synonyms='synonym_sample');
SELECT ts_lexize('syn', 'indices');
CREATE TEXT SEARCH CONFIGURATION tst (copy=simple);
ALTER TEXT SEARCH CONFIGURATION tst ALTER MAPPING FOR asciiword WITH syn;
SELECT to_tsvector('tst', 'indices');
SELECT to_tsquery('tst', 'indices');


SELECT 'indexes are very useful'::tsvector;

SELECT 'indexes are very useful'::tsvector @@ to_tsquery('tst', 'indices');


update goods_nomenclature_descriptions_oplog set document = to_tsvector(description);

-- Sample query
select * from goods_nomenclature_descriptions_oplog gndo
where document @@ to_tsquery('white<1>chocolate');

-- Sample query speed test
explain analyze
select * from goods_nomenclature_descriptions_oplog gndo
where document @@ to_tsquery('white<1>chocolate');

select * from goods_nomenclature_descriptions_oplog gndo
where document @@ to_tsquery('apparel')
order by ts_rank(document, 'apparel');

create index document_idx
on goods_nomenclature_descriptions_oplog
using GIN (document) 

alter table goods_nomenclature_descriptions_oplog 
add column document with weights

Other is treated as a stopword
Relay is treated as being the same as lay


CREATE TRIGGER update_goods_nomenclature_descriptions
AFTER INSERT OR UPDATE ON public.goods_nomenclature_descriptions_oplog
FOR EACH ROW EXECUTE PROCEDURE public.update_goods_nomenclature_description();

