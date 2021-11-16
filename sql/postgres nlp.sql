-- Create the raw data
CREATE TABLE documents  
(
    document_id SERIAL,
    document_text TEXT,
    document_tokens TSVECTOR,

    CONSTRAINT documents_pkey PRIMARY KEY (document_id)
)

-- Insert data
INSERT INTO documents (document_text) VALUES  
('Pack my box with five dozen liquor jugs.'),
('Jackdaws love my big sphinx of quartz.'),
('The five boxing wizards jump quickly.'),
('How vexingly quick daft zebras jump!'),
('Bright vixens jump; dozy fowl quack.'),
('Sphinx of black quartz, judge my vow.');


INSERT INTO documents (document_text) VALUES  
('I am using pgsql')


-- Create the vector tokens
UPDATE documents d1  
SET document_tokens = to_tsvector(d1.document_text)  
FROM documents d2;  

select * from documents;

-- Test 1: AND operator
SELECT document_id, document_text FROM documents  
WHERE document_tokens @@ to_tsquery('jump & quick'); 

-- Test 2: immediate proximity operator
SELECT document_id, document_text FROM documents  
WHERE document_tokens @@ to_tsquery('jump <-> quick');  

-- Test 3: 2-distance proximity
SELECT * FROM documents  
WHERE document_tokens @@ to_tsquery('sphinx <2> quartz'); 

SELECT document_id, document_text FROM documents  
WHERE document_tokens @@ to_tsquery('public.pg', 'pgsql'); 


