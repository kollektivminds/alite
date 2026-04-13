-- Drop tables in the correct reverse order of dependency to avoid errors
-- First, drop all junction tables and tables with foreign keys
DROP TABLE IF EXISTS lem_rels;

DROP TABLE IF EXISTS lesslists_in_modules;

DROP TABLE IF EXISTS words_in_lesslists;

DROP TABLE IF EXISTS lems_in_lesslists;

DROP TABLE IF EXISTS sent_docs;

DROP TABLE IF EXISTS lemma_defs;

DROP TABLE IF EXISTS lem_defs;

DROP TABLE IF EXISTS def_sents;

DROP TABLE IF EXISTS def_exs;

DROP TABLE IF EXISTS word_forms;

-- Next, drop the primary tables that are referenced by the ones above
DROP TABLE IF EXISTS skills;

DROP TABLE IF EXISTS user_groups;

DROP TABLE IF EXISTS users;

DROP TABLE IF EXISTS lessons_lists;

DROP TABLE IF EXISTS modules;

DROP TABLE IF EXISTS pronunciations;

DROP TABLE IF EXISTS examples;

DROP TABLE IF EXISTS definitions;

DROP TABLE IF EXISTS gram_props;

DROP TABLE IF EXISTS word_questions;

DROP TABLE IF EXISTS lexicon;

DROP TABLE IF EXISTS lemmas;

-- DROP TYPE IF EXISTS adjective_type_enum;
-- DROP TYPE IF EXISTS conj_gender_enum;
-- DROP TYPE IF EXISTS conj_person_enum;
-- DROP TYPE IF EXISTS gram_tense_enum;
-- DROP TYPE IF EXISTS pos_enum;
-- DROP TYPE IF EXISTS part_type_enum;
-- DROP TYPE IF EXISTS part_voice_enum;
-- DROP TYPE IF EXISTS subst_case_enum;
-- DROP TYPE IF EXISTS verb_type_enum;
-- DROP TYPE IF EXISTS verb_mood_enum;
-- DROP TYPE IF EXISTS verb_aspect_enum;
-- DROP TYPE IF EXISTS verb_trans_refl_enum;
-- CREATE TYPE adjective_type_enum AS ENUM ('comparative', 'superlative');
-- CREATE TYPE conj_gender_enum AS ENUM ('masculine', 'neuter', 'feminine', 'plural');
-- CREATE TYPE conj_person_enum AS ENUM ('first-person', 'second-person', 'third-person');
-- CREATE TYPE gram_tense_enum AS ENUM ('past', 'present', 'future');
-- CREATE TYPE pos_enum AS ENUM (
--     'adjective',
--     'adverb',
--     'com',
--     'interjection',
--     'noun',
--     'participle',
--     'particle',
--     'preposition',
--     'pronoun',
--     'verb',
--     'unknown'
-- );
-- CREATE TYPE part_type_enum AS ENUM ('adjectival', 'adverbial');
-- CREATE TYPE part_voice_enum AS ENUM ('active', 'passive');
-- CREATE TYPE subst_case_enum AS ENUM (
--     'nominative',
--     'genitive',
--     'accusative',
--     'dative',
--     'instrumental',
--     'prepositional',
--     'locative',
--     'vocative',
--     'partitive'
-- );
-- CREATE TYPE verb_type_enum AS ENUM ('type-I', 'type-II');
-- CREATE TYPE verb_mood_enum AS ENUM ('indicative', 'imperative');
-- CREATE TYPE verb_aspect_enum AS ENUM ('imperfective', 'perfective', 'dual');
-- CREATE TYPE verb_trans_refl_enum AS ENUM ('intransitive', 'transitive', 'reflexive');
--
-- WORDS
--
-- PRIMARY TABLE for all base forms
-- RELS INCL 
CREATE TABLE
    lemmas (
        id SERIAL PRIMARY KEY,
        lem_text VARCHAR(50) NOT NULL,
        lem_canon VARCHAR(50),
        pos VARCHAR(50) NOT NULL,
        entry_key UUID NOT NULL UNIQUE,
        subst_animacy BOOLEAN,
        verb_aspect VARCHAR(50),
        verb_conj VARCHAR(8), -- Zalizniak's classification string
        verb_type VARCHAR(50),
        verb_trans_refl VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT unique_lemma UNIQUE (id, entry_key)
    );

-- PRIMARY TABLE for all word forms involved
-- RELS INCL 
CREATE TABLE
    lexicon (
        id SERIAL PRIMARY KEY,
        lex_text VARCHAR(50) NOT NULL UNIQUE,
        lex_text_clean VARCHAR(50) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

-- PRIMARY TABLE for all grammatical combinations
-- RELS INCL 
CREATE TABLE
    gram_props (
        -- id number
        id SERIAL PRIMARY KEY,
        conj_gender VARCHAR(50),
        conj_person VARCHAR(50),
        verb_mood VARCHAR(50),
        part_type VARCHAR(50),
        part_voice VARCHAR(50),
        subst_case VARCHAR(50),
        adjv_type VARCHAR(50),
        adjv_short BOOLEAN,
        diminutive BOOLEAN,
        gram_number INT,
        gram_tense INT,
        irregular BOOLEAN,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT unique_grammar UNIQUE (
            conj_gender,
            conj_person,
            verb_mood,
            part_type,
            part_voice,
            subst_case,
            adjv_short,
            diminutive,
            gram_number,
            gram_tense
        )
    );

-- PRIMARY TABLE for word instances
-- RELS INCL 
CREATE TABLE
    word_forms (
        id SERIAL PRIMARY KEY,
        lem_id INT NOT NULL,
        lex_id INT NOT NULL,
        gram_id INT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT lemma FOREIGN KEY (lem_id) REFERENCES lemmas (id) ON DELETE CASCADE,
        CONSTRAINT lexicon FOREIGN KEY (lex_id) REFERENCES lexicon (id) ON DELETE CASCADE,
        CONSTRAINT grammar FOREIGN KEY (gram_id) REFERENCES gram_props (id) ON DELETE CASCADE
    );

-- PRIMARY TABLE for word definitions
-- RELS INCL 
CREATE TABLE
    definitions (
        id SERIAL PRIMARY KEY,
        def_text TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP UNIQUE
    );

-- PRIMARY TABLE for word definition example sentences
-- RELS INCL
CREATE TABLE
    examples (
        id SERIAL PRIMARY KEY,
        ex_text TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

-- PRIMARY TABLE for word pronunciations
-- RELS INCL
CREATE TABLE
    pronunciations (
        id SERIAL PRIMARY KEY,
        pron_text TEXT NOT NULL,
        pron_tags TEXT,
        -- 0 = ipa, 1 = romanization
        pron_type INT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

--
-- WORD JUNCTION TABLES
--
-- SECONDARY TABLE for lemma relationships (M-M)
-- RELS INCL
CREATE TABLE
    lem_rels (
        id SERIAL PRIMARY KEY,
        source_id INT NOT NULL,
        target_id INT NOT NULL,
        -- 0 = is_imperfective_pair_of, 1 = is_perfective_pair_of, 2 = is_relational_adjective_of, 3 = is_deverbal_noun_of, 4 = is_adverb_of, 5 = is_abstract_noun_of, 6 = is_synonym_of, 7 = is_anytonym_of
        rel_type INT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT id_source FOREIGN KEY (source_id) REFERENCES lemmas (id) ON DELETE CASCADE,
        CONSTRAINT id_target FOREIGN KEY (target_id) REFERENCES lemmas (id) ON DELETE CASCADE
    );

-- SECONDARY TABLE for definitions (M-M)
-- RELS INCL
CREATE TABLE
    lem_defs (
        lem_id INT NOT NULL,
        def_id INT NOT NULL,
        PRIMARY KEY (lem_id, def_id),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT lemma_definition FOREIGN KEY (lem_id) REFERENCES lemmas (id) ON DELETE CASCADE,
        CONSTRAINT definition_lemma FOREIGN KEY (def_id) REFERENCES definitions (id) ON DELETE CASCADE
    );

-- SECONDARY TABLE for word definitions and their example sentences
-- RELS INCL
CREATE TABLE
    def_exs (
        def_id INT NOT NULL,
        ex_id INT NOT NULL,
        PRIMARY KEY (def_id, ex_id),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT definition_example FOREIGN KEY (def_id) REFERENCES definitions (id) ON DELETE CASCADE,
        CONSTRAINT example_definition FOREIGN KEY (ex_id) REFERENCES examples (id) ON DELETE CASCADE
    );

--
-- WORD ORGANIZATION
--
-- PRIMARY TABLE for textbook modules
-- RELS INCL 
CREATE TABLE
    modules (
        id SERIAL PRIMARY KEY,
        module_name VARCHAR(10) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

-- PRIMARY TABLE for lessons and custom word lists
-- RELS INCL 
CREATE TABLE
    lessons_lists (
        id SERIAL PRIMARY KEY,
        title VARCHAR(50) NOT NULL,
        topic TEXT,
        -- 0 = lesson, 1 = native list, 2 = student list
        is_type INT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

-- SECONDARY TABLE for lessons/lists in modules
-- RELS INCL 
CREATE TABLE
    lesslists_in_modules (
        lesslist_id INT NOT NULL,
        module_id INT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (lesslist_id, module_id),
        CONSTRAINT lessons_lists FOREIGN KEY (lesslist_id) REFERENCES lessons_lists (id) ON DELETE CASCADE,
        CONSTRAINT module FOREIGN KEY (module_id) REFERENCES modules (id) ON DELETE CASCADE
    );

-- SECONDARY TABLE for words in lessons/lists
-- RELS INCL 
CREATE TABLE
    lems_in_lesslists (
        lem_id INT NOT NULL,
        lesslist_id INT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (lem_id, lesslist_id),
        CONSTRAINT lemma FOREIGN KEY (lem_id) REFERENCES lemmas (id) ON DELETE CASCADE,
        CONSTRAINT lessons_lists FOREIGN KEY (lesslist_id) REFERENCES lessons_lists (id) ON DELETE CASCADE
    );