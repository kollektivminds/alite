-- Drop tables in the correct reverse order of dependency to avoid errors
-- First, drop all junction tables and tables with foreign keys
DROP TABLE IF EXISTS user_experiments;
DROP TABLE IF EXISTS student_skill_mastery;
DROP TABLE IF EXISTS skills_in_word_questions;
DROP TABLE IF EXISTS student_decisions;
DROP TABLE IF EXISTS student_responses;
DROP TABLE IF EXISTS question_sessions;
DROP TABLE IF EXISTS users_in_groups;
DROP TABLE IF EXISTS lesslists_in_modules;
DROP TABLE IF EXISTS words_in_lesslists;
-- remove
DROP TABLE IF EXISTS lems_in_lesslists;
DROP TABLE IF EXISTS sent_docs;
DROP TABLE IF EXISTS verb_pairs;
DROP TABLE IF EXISTS lemma_defs;
-- remove
DROP TABLE IF EXISTS lem_defs;
DROP TABLE IF EXISTS def_sents;
DROP TABLE IF EXISTS word_forms;
-- Next, drop the primary tables that are referenced by the ones above
DROP TABLE IF EXISTS skills;
DROP TABLE IF EXISTS user_groups;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS lessons_lists;
DROP TABLE IF EXISTS modules;
DROP TABLE IF EXISTS pronunciations;
DROP TABLE IF EXISTS def_examples;
-- remove
DROP TABLE IF EXISTS def_exs;
DROP TABLE IF EXISTS definitions;
DROP TABLE IF EXISTS gram_props;
DROP TABLE IF EXISTS questions;
-- remove
DROP TABLE IF EXISTS items;
DROP TABLE IF EXISTS word_questions;
DROP TABLE IF EXISTS lexicon;
DROP TABLE IF EXISTS lemmas;
--
-- WORDS
--

-- PRIMARY TABLE for all base forms
-- RELS INCL 
CREATE TABLE lemmas (
    id SERIAL PRIMARY KEY,
    lem_text VARCHAR(50) NOT NULL,
    lem_canon VARCHAR(50),
    -- 0 = adjective, 1 = adverb, 2 = noun, 3 = number, 4 = participle, 5 = pronoun, 6 = verb
    pos INT NOT NULL,
    entry_key UUID NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_lemma UNIQUE (id, entry_key)
);
-- PRIMARY TABLE for all word forms involved
-- RELS INCL 
CREATE TABLE lexicon (
    id SERIAL PRIMARY KEY,
    lex_text VARCHAR(50) NOT NULL UNIQUE,
    lex_text_clean VARCHAR(50) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    verb_type INT,
    -- 0 = indicative, 1 = imperative
    verb_mood INT,
    -- 0 = is transitive, 1 = is reflexive,
    -- 2 = is neither transitive nor reflexive
    verb_trans_refl INT,
    -- 1 = first, 2 = second, 3 = third
    verb_person INT,
    -- 0 = adjectival, 1 = adverbial
    part_type INT,
    -- 0 = active, 1 = passive
    part_voice INT,
    -- 0 = nominative, 1 = genitive, 2 = accusative,
    -- 3 = dative, 4 = instrumental, 5 = prepositional, 
    -- 6 = vocative, 7 = locative, 8 = partitive
    subst_case INT,
    -- False, True
    subst_animacy BOOLEAN,
    -- False, True
    adjv_short BOOLEAN,
    --False, True
    diminutive BOOLEAN,
    -- 0 = masculine, 1 = neuter, 2 = feminine, 3 = dual M/F
    gram_gender INT,
    -- 0 = singular, 1 = plural, 2 = dual
    gram_number INT,
    -- 0 = past, 1 = present, 2 = future
    gram_tense INT,
    -- False, True
    -- not included in unique constraint?
    irregular BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_grammar UNIQUE (
        verb_aspect,
        verb_conj,
        verb_type,
        verb_mood,
        verb_trans_refl,
        verb_person,
        part_type,
        part_voice,
        subst_case,
        subst_animacy,
        adjv_short,
        diminutive,
        gram_gender,
        gram_number,
        gram_tense
    )
);
-- PRIMARY TABLE for word instances
-- RELS INCL 
CREATE TABLE word_forms (
    id SERIAL PRIMARY KEY,
    lem_id INT NOT NULL,
    lex_id INT NOT NULL,
    gram_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT lemma FOREIGN KEY (lem_id) REFERENCES lemmas(id) ON DELETE CASCADE,
    CONSTRAINT lexicon FOREIGN KEY (lex_id) REFERENCES lexicon(id) ON DELETE CASCADE,
    CONSTRAINT grammar FOREIGN KEY (gram_id) REFERENCES gram_props(id) ON DELETE CASCADE
);
-- PRIMARY TABLE for word definitions
-- RELS INCL 
CREATE TABLE definitions (
    id SERIAL PRIMARY KEY,
    def_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP UNIQUE
);
-- PRIMARY TABLE for word definition example sentences
-- RELS INCL
CREATE TABLE examples (
    id SERIAL PRIMARY KEY,
    ex_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- PRIMARY TABLE for word pronunciations
-- RELS INCL
CREATE TABLE pronunciations (
    id SERIAL PRIMARY KEY,
    pron_text TEXT NOT NULL,
    pron_type TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
--
-- WORD JUNCTION TABLES
--

-- SECONDARY TABLE for lemma relationships (M-M)
-- RELS INCL
CREATE TABLE lem_rels (
    id SERIAL PRIMARY KEY,
    source_id INT NOT NULL,
    target_id INT NOT NULL,
    -- 0 = 
    rel_type INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT id_source FOREIGN KEY (source_id) REFERENCES lemmas(id) ON DELETE CASCADE,
    CONSTRAINT id_target FOREIGN KEY (target_id) REFERENCES lemmas(id) ON DELETE CASCADE
);
-- SECONDARY TABLE for definitions (M-M)
-- RELS INCL
CREATE TABLE lem_defs (
    lem_id INT NOT NULL,
    def_id INT NOT NULL,
    PRIMARY KEY (lem_id, def_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT lemma_definition FOREIGN KEY (lem_id) REFERENCES lemmas(id) ON DELETE CASCADE,
    CONSTRAINT definition_lemma FOREIGN KEY (def_id) REFERENCES definitions(id) ON DELETE CASCADE
);
-- SECONDARY TABLE for word definitions and their example sentences
-- RELS INCL
CREATE TABLE def_exs (
    def_id INT NOT NULL,
    ex_id INT NOT NULL,
    PRIMARY KEY (def_id, ex_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT definition_example FOREIGN KEY (def_id) REFERENCES definitions(id) ON DELETE CASCADE,
    CONSTRAINT example_definition FOREIGN KEY (ex_id) REFERENCES examples(id) ON DELETE CASCADE
);
--
-- WORD ORGANIZATION
--

-- PRIMARY TABLE for textbook modules
-- RELS INCL 
CREATE TABLE modules (
    id SERIAL PRIMARY KEY,
    module_name VARCHAR(10) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- PRIMARY TABLE for lessons and custom word lists
-- RELS INCL 
CREATE TABLE lessons_lists (
    id SERIAL PRIMARY KEY,
    title VARCHAR(50) NOT NULL,
    topic TEXT,
    -- 0 = lesson, 1 = native list, 2 = student list
    is_type INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- SECONDARY TABLE for lessons/lists in modules
-- RELS INCL 
CREATE TABLE lesslists_in_modules (
    lesslist_id INT NOT NULL,
    module_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (lesslist_id, module_id),
    CONSTRAINT lessons_lists FOREIGN KEY (lesslist_id) REFERENCES lessons_lists(id) ON DELETE CASCADE,
    CONSTRAINT module FOREIGN KEY (module_id) REFERENCES modules(id) ON DELETE CASCADE
);
-- SECONDARY TABLE for words in lessons/lists
-- RELS INCL 
CREATE TABLE lems_in_lesslists (
    lem_id INT NOT NULL,
    lesslist_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (lem_id, lesslist_id),
    CONSTRAINT lemma FOREIGN KEY (lem_id) REFERENCES lemmas(id) ON DELETE CASCADE,
    CONSTRAINT lessons_lists FOREIGN KEY (lesslist_id) REFERENCES lessons_lists(id) ON DELETE CASCADE
);
--
-- USERS
--

-- PRIMARY TABLE for users
-- RELS INCL 
-- CREATE TABLE users (
--     id SERIAL PRIMARY KEY,
--     username VARCHAR(50) UNIQUE,
--     privileged BOOLEAN DEFAULT FALSE,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );
-- PRIMARY TABLE for user groups
-- RELS INCL 
-- CREATE TABLE user_groups (
--     id SERIAL PRIMARY KEY,
--     group_name VARCHAR(50) UNIQUE
-- );
-- SECONDARY TABLE for users' belonging to groups
-- RELS INCL 
-- CREATE TABLE users_in_groups (
--     user_id INT NOT NULL,
--     group_id INT NOT NULL,
--     PRIMARY KEY (user_id, group_id),
--     CONSTRAINT group_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
--     CONSTRAINT user_group FOREIGN KEY (group_id) REFERENCES user_groups(id) ON DELETE CASCADE
-- );
--
-- ITEMS
--

-- CREATE TABLE items (
--     id SERIAL PRIMARY KEY,
--     item_type VARCHAR(50) NOT NULL,
--     item_text TEXT NOT NULL,
--     choices JSONB NOT NULL,
--     -- For multiple choice options
--     correct_answer TEXT NOT NULL,
--     lem_id INT,
--     -- Optional link to a specific word
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     difficulty FLOAT,
--     -- IRT 'b' parameter
--     discrimination FLOAT,
--     -- IRT 'a' parameter
--     guess_probability FLOAT,
--     -- IRT 'c' parameter
--     CONSTRAINT fk_lemma FOREIGN KEY (lem_id) REFERENCES lemmas(id) ON DELETE CASCADE
-- );
--
-- SESSIONS
--

-- CREATE TABLE question_sessions (
--     id SERIAL PRIMARY KEY,
--     user_id INT NOT NULL,
--     session_start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     session_end_time TIMESTAMP,
--     CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
-- );
--
-- STUDENT RESPONSES
--

-- CREATE TABLE student_responses (
--     id SERIAL PRIMARY KEY,
--     session_id INT NOT NULL,
--     question_id INT NOT NULL,
--     student_answer TEXT,
--     is_correct BOOLEAN,
--     response_time_ms INT,
--     submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     CONSTRAINT fk_session FOREIGN KEY (session_id) REFERENCES question_sessions(id) ON DELETE CASCADE,
--     CONSTRAINT fk_question FOREIGN KEY (question_id) REFERENCES word_questions(id) ON DELETE CASCADE
-- );
--
-- STUDENT DECISIONS
--

-- CREATE TABLE student_decisions (
--     id SERIAL PRIMARY KEY,
--     user_id INT NOT NULL,
--     decision_type VARCHAR(100) NOT NULL,
--     -- E.g., 'selected_topic', 'chose_question_format'
--     decision_value TEXT NOT NULL,
--     made_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
-- );
--
-- SKILLS
--

-- CREATE TABLE skills (
--     id SERIAL PRIMARY KEY,
--     skill_name VARCHAR(255) NOT NULL UNIQUE,
--     skill_description TEXT,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );
-- CREATE TABLE skills_in_word_questions (
--     question_id INT NOT NULL,
--     skill_id INT NOT NULL,
--     PRIMARY KEY (question_id, skill_id),
--     CONSTRAINT fk_question FOREIGN KEY (question_id) REFERENCES word_questions(id) ON DELETE CASCADE,
--     CONSTRAINT fk_skill FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
-- );
-- CREATE TABLE student_skill_mastery (
--     id SERIAL PRIMARY KEY,
--     user_id INT NOT NULL,
--     skill_id INT NOT NULL,
--     mastery_level FLOAT DEFAULT 0.0,
--     p_learn FLOAT,
--     -- BKT: Probability of learning
--     p_guess FLOAT,
--     -- BKT: Probability of guessing
--     p_slip FLOAT,
--     -- BKT: Probability of slipping
--     last_seen_at TIMESTAMP,
--     next_review_at TIMESTAMP,
--     -- For spaced repetition
--     CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
--     CONSTRAINT fk_skill FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE,
--     UNIQUE (user_id, skill_id)
-- );
--
-- EXPERIMENTS
--

-- CREATE TABLE user_experiments (
--     id SERIAL PRIMARY KEY,
--     user_id INT NOT NULL,
--     experiment_name VARCHAR(255) NOT NULL,
--     variant_name VARCHAR(255) NOT NULL,
--     assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
--     UNIQUE (user_id, experiment_name)
-- );