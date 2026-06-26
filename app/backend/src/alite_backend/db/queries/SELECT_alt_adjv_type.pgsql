SELECT
    lex.lex_text,
    lex.lex_text_clean,
    gp.alt_adjv_type
FROM lexicon lex
JOIN word_forms wf
    ON lex.id = wf.lex_id
JOIN lemmas lem
    ON lem.id = wf.lem_id
JOIN gram_props gp
    ON wf.gram_id = gp.id
WHERE lem.pos = 'ADJECTIVE'
AND gp.alt_adjv_type IS NOT NULL
AND gp.alt_adjv_type != 'SHORT';