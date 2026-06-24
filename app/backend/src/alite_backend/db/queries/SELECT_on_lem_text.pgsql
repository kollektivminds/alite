SELECT 
    l.id AS lemma_id,
    l.lem_text,
    lex.*,  -- In production, replace * with explicit column names to reduce memory overhead
    gp.*,
    wf.*
FROM lemmas l
LEFT JOIN word_forms wf 
    ON l.id = wf.lem_id
LEFT JOIN gram_props gp 
    ON wf.gram_id = gp.id
LEFT JOIN lexicon lex 
    ON wf.lex_id = lex.id
WHERE l.pos = 'ручка';