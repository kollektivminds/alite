-- Drop tables in the correct reverse order of dependency to avoid errors
-- First, drop all junction tables and tables with foreign keys
DROP TABLE IF EXISTS users_in_groups;
DROP TABLE IF EXISTS lesslists_in_modules;
DROP TABLE IF EXISTS words_in_lists;
DROP TABLE IF EXISTS verb_pairs;
DROP TABLE IF EXISTS lemma_defs;
DROP TABLE IF EXISTS defs_in_sents;
DROP TABLE IF EXISTS word_forms;
DROP TABLE IF EXISTS defs_in_sents;
-- Next, drop tables that are referenced by the ones above
DROP TABLE IF EXISTS user_groups;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS lessons_lists;
DROP TABLE IF EXISTS modules;
DROP TABLE IF EXISTS def_sentences;
DROP TABLE IF EXISTS definitions;
DROP TABLE IF EXISTS gram_props;
DROP TABLE IF EXISTS lemmas;
DROP TABLE IF EXISTS lexicon;
--
-- WORDS
--

-- PRIMARY TABLE for all word forms involved
-- RELS INCL 
CREATE TABLE lexicon (
    id SERIAL PRIMARY KEY,
    lex_text VARCHAR(50) NOT NULL UNIQUE
    lex_text_clean VARCHAR(50) NOT NULL UNIQUE
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- PRIMARY TABLE for all base forms
-- RELS INCL 
CREATE TABLE lemmas (
    id SERIAL PRIMARY KEY,
    lem_text VARCHAR(50) NOT NULL,
    -- 0 = adjective, 1 = adverb, 2 = noun, 3 = number, 4 = participle, 5 = pronoun, 6 = verb
    pos INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    CONSTRAINT unique_lemma UNIQUE (lemma_text, part_of_speech)
);
-- PRIMARY TABLE for all grammatical combinations
-- RELS INCL 
CREATE TABLE gram_props (
    -- id number
    id SERIAL PRIMARY KEY,
    -- 0 = imperfective, 1 = perfective, 2 = dual
    verb_aspect INT,
    -- Zalizniak's classification string
    verb_conj VARCHAR(4),
    -- 1 = Type I, 2 = Type II
    verb_conj_type INT,
    -- False, True
    verb_infinitive BOOLEAN,
    -- 0 = indicative, 1 = imperative
    verb_mood INT,
    -- 0 = has transitivity, 1 = is reflexive,
    -- 2 = is neither transitive nor reflexive
    verb_trans_refl INT,
    -- 1 = first, 2 = second, 3 = third
    verb_conj_person INT,
    -- 0 = adjectival, 1 = adverbial
    part_type INT,
    -- 0 = active, 1 = passive
    part_voice INT,
    -- from lemmas
    part_parent_verb_id INT,
    -- 0 = nominative, 1 = genitive, 2 = accusative,
    -- 3 = dative, 4 = instrumental, 5 = prepositional, 
    -- 6 = vocative, 7 = locative, 8 = partitive
    subst_case INT,
    -- False, True
    subst_animacy BOOLEAN,
    -- False, True
    adjv_short BOOLEAN,
    -- 0 = masculine, 1 = femine, 2 = neuter, 3 = dual M/F
    gram_gender INT,
    -- 0 = singular, 1 = plural, 2 = dual
    gram_number INT,
    -- False, True
    gram_past BOOLEAN,
    --#TODO verify this
    --False, True
    noun_dimun BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    CONSTRAINT unique_grammar UNIQUE (
        verb_aspect,
        verb_conj,
        verb_conj_type,
        verb_infinitive,
        verb_mood,
        verb_trans_refl,
        verb_conj_person,
        part_type,
        part_voice,
        part_parent_verb_id,
        subst_case,
        subst_animacy,
        adjv_short,
        gram_gender,
        gram_number,
        gram_past,
        noun_dimun
    ),
    CONSTRAINT part_parent_verb FOREIGN KEY (part_parent_verb_id) REFERENCES lemmas(id) ON DELETE CASCADE
);
-- PRIMARY TABLE for word instances
-- RELS INCL 
CREATE TABLE word_forms (
    id SERIAL PRIMARY KEY,
    lemma_id INT NOT NULL,
    lexicon_id INT NOT NULL,
    grammar_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    CONSTRAINT lemma FOREIGN KEY (lemma_id) REFERENCES lemmas(id) ON DELETE CASCADE,
    CONSTRAINT lexicon FOREIGN KEY (lexicon_id) REFERENCES lexicon(id) ON DELETE CASCADE,
    CONSTRAINT grammar FOREIGN KEY (grammar_id) REFERENCES gram_props(id) ON DELETE CASCADE
);
-- PRIMARY TABLE for word definitions
-- RELS INCL 
CREATE TABLE definitions (
    id SERIAL PRIMARY KEY,
    def_text TEXT NOT NULL UNIQUE
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- PRIMARY TABLE for word definition example sentences
-- RELS INCL
CREATE TABLE def_sentences (
    id SERIAL PRIMARY KEY,
    sent_text TEXT NOT NULL UNIQUE
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- SECONDARY TABLE for word definitions and their example sentences
-- RELS INCL
CREATE TABLE defs_in_sents (
    def_id INT NOT NULL,
    sent_id INT NOT NULL,
    PRIMARY KEY (def_id, sent_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    CONSTRAINT def_sent FOREIGN KEY (sent_id) REFERENCES def_sentences(id) ON DELETE CASCADE,
    CONSTRAINT sent_def FOREIGN KEY (def_id) REFERENCES definitions(id) ON DELETE CASCADE
);
--
-- WORD JUNCTION TABLES
--

-- SECONDARY TABLE for aspect pairs (M-M)
-- RELS INCL
CREATE TABLE verb_pairs (
    imperfective_verb_id INT NOT NULL,
    perfective_verb_id INT NOT NULL,
    PRIMARY KEY (imperfective_verb_id, perfective_verb_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    CONSTRAINT imperfective_verb FOREIGN KEY (imperfective_verb_id) REFERENCES lemmas(id) ON DELETE CASCADE,
    CONSTRAINT perfective_verb FOREIGN KEY (perfective_verb_id) REFERENCES lemmas(id) ON DELETE CASCADE
);
-- SECONDARY TABLE for definitions (M-M)
-- RELS INCL
CREATE TABLE lemma_defs (
    lemma_id INT NOT NULL,
    def_id INT NOT NULL,
    PRIMARY KEY (lemma_id, definition_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    CONSTRAINT lemma_of_definition FOREIGN KEY (lemma_id) REFERENCES lemmas(id) ON DELETE CASCADE,
    CONSTRAINT definition_of_lemma FOREIGN KEY (definition_id) REFERENCES definitions(id) ON DELETE CASCADE
);
--
-- WORD ORGANIZATION
--

-- PRIMARY TABLE for textbook modules
-- RELS INCL 
CREATE TABLE modules (
    id SERIAL PRIMARY KEY,
    module_name VARCHAR(10) NOT NULL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- PRIMARY TABLE for lessons and custom word lists
-- RELS INCL 
CREATE TABLE lessons_lists (
    id SERIAL PRIMARY KEY,
    lesslist_name VARCHAR(50) NOT NULL,
    topic TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- SECONDARY TABLE for lessons/lists in modules
-- RELS INCL 
CREATE TABLE lesslists_in_modules (
    lesslist_id INT NOT NULL,
    module_id INT NOT NULL,
    PRIMARY KEY (lesslist_id, module_id),
    CONSTRAINT lessons_lists FOREIGN KEY (lesslist_id) REFERENCES lessons_lists(id) ON DELETE CASCADE,
    CONSTRAINT module FOREIGN KEY (module_id) REFERENCES modules(id) ON DELETE CASCADE
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- SECONDARY TABLE for words in lessons/lists
-- RELS INCL 
CREATE TABLE words_in_lesslists (
    lemma_id INT NOT NULL,
    lesslist_id INT NOT NULL,
    PRIMARY KEY (word_id, lesslist_id),
    CONSTRAINT word FOREIGN KEY (lemma_id) REFERENCES lemmas(id) ON DELETE CASCADE,
    CONSTRAINT lessons_lists FOREIGN KEY (lesslist_id) REFERENCES lessons_lists(id) ON DELETE CASCADE
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
--
-- SENTENCES
--

-- PRIMARY TABLE for 
-- RELS INCL
CREATE TABLE sent_docs (
    id SERIAL PRIMARY KEY,
    author TEXT NOT NULL,
    date DATE NOT NULL,
    source TEXT NOT NULL,
    title TEXT NOT NULL,
    comment TEXT NOT NULL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- PRIMARY TABLE for 
-- RELS INCL
CREATE TABLE sent_docs (
    id SERIAL PRIMARY KEY,
    author TEXT NOT NULL,
    date DATE NOT NULL,
    source TEXT NOT NULL,
    title TEXT NOT NULL,
    comment TEXT NOT NULL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

--
-- USERS
--

-- PRIMARY TABLE for users
-- RELS INCL 
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE,
    privileged BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- PRIMARY TABLE for user groups
-- RELS INCL 
CREATE TABLE user_groups (
    id SERIAL PRIMARY KEY,
    group_name VARCHAR(50) UNIQUE
);
-- SECONDARY TABLE for users' belonging to groups
-- RELS INCL 
CREATE TABLE users_in_groups (
    user_id INT NOT NULL,
    group_id INT NOT NULL,
    PRIMARY KEY (user_id, group_id),
    CONSTRAINT group_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT user_group FOREIGN KEY (group_id) REFERENCES user_groups(id) ON DELETE CASCADE
);