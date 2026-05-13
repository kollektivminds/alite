-- Drop tables in the correct reverse order of dependency to avoid errors
-- First, drop all junction tables and tables with foreign keys
DROP TABLE IF EXISTS users_in_groups;

DROP TABLE IF EXISTS lookup_queue;

DROP TABLE IF EXISTS lem_rels;

DROP TABLE IF EXISTS lesslists_in_modules;

DROP TABLE IF EXISTS less_lists_in_mods;

DROP TABLE IF EXISTS lems_in_less_lists;

DROP TABLE IF EXISTS lems_in_lesslists;

DROP TABLE IF EXISTS sent_docs;

DROP TABLE IF EXISTS lem_defs;

DROP TABLE IF EXISTS def_exs;

DROP TABLE IF EXISTS word_forms;

-- Next, drop the primary tables that are referenced by the ones above
DROP TABLE IF EXISTS skills;

DROP TABLE IF EXISTS user_groups;

DROP TABLE IF EXISTS lessons_lists;

DROP TABLE IF EXISTS users;

DROP TABLE IF EXISTS modules;

DROP TABLE IF EXISTS pronunciations;

DROP TABLE IF EXISTS examples;

DROP TABLE IF EXISTS definitions;

DROP TABLE IF EXISTS gram_props;

DROP TABLE IF EXISTS word_questions;

DROP TABLE IF EXISTS lexicon;

DROP TABLE IF EXISTS lemmas;

-- DROP TYPE IF EXISTS adjective_type_enum
-- DROP TYPE IF EXISTS conj_gender_enum
-- DROP TYPE IF EXISTS conj_person_enum
-- DROP TYPE IF EXISTS gram_tense_enum
-- DROP TYPE IF EXISTS pos_enum
-- DROP TYPE IF EXISTS part_type_enum
-- DROP TYPE IF EXISTS part_voice_enum
-- DROP TYPE IF EXISTS subst_case_enum
-- DROP TYPE IF EXISTS verb_type_enum
-- DROP TYPE IF EXISTS verb_mood_enum
-- DROP TYPE IF EXISTS verb_aspect_enum
-- DROP TYPE IF EXISTS verb_trans_refl_enum
-- CREATE TYPE adjective_type_enum AS ENUM ('comparative', 'superlative')
-- CREATE TYPE conj_gender_enum AS ENUM ('masculine', 'neuter', 'feminine', 'plural')
-- CREATE TYPE conj_person_enum AS ENUM ('first-person', 'second-person', 'third-person')
-- CREATE TYPE gram_tense_enum AS ENUM ('past', 'present', 'future')
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
-- )
-- CREATE TYPE part_type_enum AS ENUM ('adjectival', 'adverbial')
-- CREATE TYPE part_voice_enum AS ENUM ('active', 'passive')
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
-- )
-- CREATE TYPE verb_type_enum AS ENUM ('type-I', 'type-II')
-- CREATE TYPE verb_mood_enum AS ENUM ('indicative', 'imperative')
-- CREATE TYPE verb_aspect_enum AS ENUM ('imperfective', 'perfective', 'dual')
-- CREATE TYPE verb_trans_refl_enum AS ENUM ('intransitive', 'transitive', 'reflexive')
CREATE EXTENSION IF NOT EXISTS citext;

--
-- WORDS
--
-- PRIMARY TABLE for all base forms
-- RELS INCL 
CREATE TABLE
    lemmas (
        -- ALL / MOST WILL HAVE
        id SERIAL PRIMARY KEY,
        entry_key UUID NOT NULL UNIQUE,
        lem_text VARCHAR(50) NOT NULL,
        lem_canon VARCHAR(50),
        pos VARCHAR(50) NOT NULL,
        -- SPARSE
        noun_gender VARCHAR(50),
        subst_animacy BOOLEAN,
        verb_aspect VARCHAR(50),
        verb_conj VARCHAR(16), -- ZALIZNIAK'S CLASSIFICATION
        verb_type VARCHAR(8), -- TYPE-I / TYPE-II FROM verb_conj
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

-- PRIMARY TABLE for all grammatical combinations (NOT COVERED IN LEMMA)
-- RELS INCL 
CREATE TABLE
    gram_props (
        id SERIAL PRIMARY KEY,
        -- GENERAL GRAMMAR
        gram_tense VARCHAR(50),
        irregular BOOLEAN,
        gram_num VARCHAR(50),
        -- VERBS
        conj_gender VARCHAR(50),
        conj_person VARCHAR(50),
        verb_mood VARCHAR(50),
        -- SUBSTANTIVES (NOUNS, ADJECTIVES, NUMERALS, PARTICIPLES)
        subst_case VARCHAR(50),
        alt_adjv_type VARCHAR(50),
        alt_noun_type VARCHAR(50),
        -- PARTICIPLES
        part_type VARCHAR(50),
        part_voice VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT unique_grammar UNIQUE (
            gram_tense,
            gram_num,
            conj_gender,
            conj_person,
            verb_mood,
            subst_case,
            alt_adjv_type,
            alt_noun_type,
            part_type,
            part_voice
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
        def_tags TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        pron_type VARCHAR(50) NOT NULL,
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
        rel_type VARCHAR(16) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT id_source FOREIGN KEY (source_id) REFERENCES lemmas (id) ON DELETE CASCADE,
        CONSTRAINT id_target FOREIGN KEY (target_id) REFERENCES lemmas (id) ON DELETE CASCADE
    );

-- PRIMARY TABLE for a lookup queue for lemma rels
-- RELS INCL
CREATE TABLE
    lookup_queue (
        id SERIAL PRIMARY KEY,
        target_lem VARCHAR(50) NOT NULL,
        target_id INT,
        source_id INT NOT NULL,
        rel_type VARCHAR(48) NOT NULL,
        lookup_status VARCHAR(16),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT source_id FOREIGN KEY (source_id) REFERENCES lemmas (id) ON DELETE CASCADE,
        CONSTRAINT target_id FOREIGN KEY (target_id) REFERENCES lemmas (id) ON DELETE CASCADE
    );

-- SECONDARY TABLE for definitions (M-M)
-- RELS INCL
CREATE TABLE
    lem_defs (
        lem_id INT NOT NULL,
        def_id INT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (lem_id, def_id),
        CONSTRAINT lemma_definition FOREIGN KEY (lem_id) REFERENCES lemmas (id) ON DELETE CASCADE,
        CONSTRAINT definition_lemma FOREIGN KEY (def_id) REFERENCES definitions (id) ON DELETE CASCADE
    );

-- SECONDARY TABLE for word definitions and their example sentences
-- RELS INCL
CREATE TABLE
    def_exs (
        def_id INT NOT NULL,
        ex_id INT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (def_id, ex_id),
        CONSTRAINT definition_example FOREIGN KEY (def_id) REFERENCES definitions (id) ON DELETE CASCADE,
        CONSTRAINT example_definition FOREIGN KEY (ex_id) REFERENCES examples (id) ON DELETE CASCADE
    );

--
-- USER ORGANIZATION
--
CREATE TABLE
    users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) NOT NULL UNIQUE,
        alias VARCHAR(25),
        user_role VARCHAR(50),
        email citext,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT email_format_check CHECK (email ~* '^\\S+@\\S+\\.\\S+$')
    );

CREATE TABLE
    user_groups (
        id SERIAL PRIMARY KEY,
        group_name VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

CREATE TABLE
    users_in_groups (
        user_id INT NOT NULL,
        group_id INT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, group_id),
        CONSTRAINT id_user FOREIGN KEY (user_id) REFERENCES users (id),
        CONSTRAINT id_group FOREIGN KEY (group_id) REFERENCES user_groups (id)
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
        title VARCHAR(50) NOT NULL UNIQUE,
        topic TEXT,
        owner_id INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT user_owner_id FOREIGN KEY (owner_id) REFERENCES users (id)
    );

-- SECONDARY TABLE for lessons/lists in modules
-- RELS INCL 
CREATE TABLE
    less_lists_in_mods (
        mod_id INT NOT NULL,
        less_list_id INT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (less_list_id, mod_id),
        CONSTRAINT lessons_lists FOREIGN KEY (less_list_id) REFERENCES lessons_lists (id) ON DELETE CASCADE,
        CONSTRAINT module FOREIGN KEY (mod_id) REFERENCES modules (id) ON DELETE CASCADE
    );

-- SECONDARY TABLE for words in lessons/lists
-- RELS INCL 
CREATE TABLE
    lems_in_less_lists (
        lem_id INT NOT NULL,
        less_list_id INT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (lem_id, less_list_id),
        CONSTRAINT lemma FOREIGN KEY (lem_id) REFERENCES lemmas (id) ON DELETE CASCADE,
        CONSTRAINT lessons_lists FOREIGN KEY (less_list_id) REFERENCES lessons_lists (id) ON DELETE CASCADE
    );