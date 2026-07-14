# ALITE Database Schema

- [ALITE Database Schema](#alite-database-schema)
  - [Word Tables](#word-tables)
    - [01. lemmas](#01-lemmas)
      - [table](#table)
      - [controlled vocab](#controlled-vocab)
    - [00. lexicon](#00-lexicon)
    - [02. gram\_props](#02-gram_props)
      - [table](#table-1)
      - [controlled vocab](#controlled-vocab-1)
    - [03. word\_forms](#03-word_forms)
  - [Sentence Tables](#sentence-tables)
    - [04. sent\_docs](#04-sent_docs)
    - [05. sentences](#05-sentences)
    - [06. sent\_doc\_sents](#06-sent_doc_sents)
    - [07. sentence\_lexemes](#07-sentence_lexemes)
  - [Paragraph Tables](#paragraph-tables)
    - [08. definitions](#08-definitions)
    - [09. def\_examples](#09-def_examples)
    - [10. def\_sents](#10-def_sents)
    - [11. lemma\_defs](#11-lemma_defs)
    - [12. verb\_pairs](#12-verb_pairs)
  - [Vocab Organization](#vocab-organization)
    - [13. modules](#13-modules)
    - [14. lessons\_lists](#14-lessons_lists)
    - [15. lesslists\_in\_modules](#15-lesslists_in_modules)
    - [16. words\_in\_leslists](#16-words_in_leslists)
  - [users](#users)
    - [17. users](#17-users)
    - [18. user\_groups](#18-user_groups)
    - [19. users\_in\_groups](#19-users_in_groups)
  - [questions \& answers](#questions--answers)
    - [20. questions](#20-questions)
    - [21. question\_sessions](#21-question_sessions)
    - [22. student\_responses](#22-student_responses)
    - [23. student\_decisions](#23-student_decisions)
  - [skills](#skills)
    - [24. skills](#24-skills)
      - [table](#table-2)
      - [controlled vocab](#controlled-vocab-2)
    - [25. skills\_in\_questions](#25-skills_in_questions)
    - [26. student\_skill\_mastery](#26-student_skill_mastery)
  - [experiments](#experiments)
    - [27. user\_experiments](#27-user_experiments)

## Word Tables

### 01. lemmas

Base forms with part of speech

#### table

| name            | type        | constraints     | description    |
| --------------- | ----------- | --------------- | -------------- |
| id              | SERIAL      | PRIMARY KEY     |                |
| entry_key       | UUID        | NOT NULL UNIQUE |                |
| lem_text        | INT         | NOT NULL        | part of speech |
| lem_canon       | INT         |                 | part of speech |
| pos             | VARCHAR(48) | *controlled*    | part of speech |
| noun_gender     | VARCHAR(48) | *controlled*    | part of speech |
| noun_animacy   | BOOLEAN     |                 | part of speech |
| verb_aspect     | VARCHAR(48) | *controlled*    | part of speech |
| verb_conj       | VARCHAR(16) |                 | part of speech |
| verb_type       | VARCHAR(8)  | *controlled*    | part of speech |
| verb_trans_refl | VARCHAR(48) | *controlled*    | part of speech |
| created_at      | INT         |                 | part of speech |

#### controlled vocab

| **property**        | **value**    |
| ------------------- | ------------ |
| **pos**             | adjective    |
|                     | adverb       |
|                     | com          |
|                     | conjunction  |
|                     | interjection |
|                     | noun         |
|                     | number       |
|                     | participle   |
|                     | particle     |
|                     | preposition  |
|                     | pronoun      |
|                     | verb         |
|                     | unknown      |
|                     |              |
| **noun_gender**     | masculine    |
|                     | neuter       |
|                     | feminine     |
|                     |              |
| **verb_aspect**     | imperfective |
|                     | perfective   |
|                     |              |
| **verb_type**       | Type-I       |
|                     | Type-II      |
|                     |              |
| **verb_trans_refl** | intransitive |
|                     | transitive   |
|                     | reflexive    |

### 00. lexicon

Forms of lemmas

| name           | type        | constraints     | description                     |
| -------------- | ----------- | --------------- | ------------------------------- |
| id             | SERIAL      | PRIMARY KEY     |                                 |
| lex_text       | VARCHAR(50) | NOT NULL UNIQUE | lexeme text with accent mark    |
| lex_text_clean | VARCHAR(50) | NOT NULL UNIQUE | lexeme text without accent mark |

### 02. gram_props

Grammar property combinations of lemmas

#### table

| name             | type       | constraints  | description                         |
| ---------------- | ---------- | ------------ | ----------------------------------- |
| id               | SERIAL     | PRIMARY KEY  |                                     |
| verb_aspect      | INT        | *controlled* | verb aspect                         |
| verb_conj        | VARCHAR(4) |              | verb conjugation (Zalizniak)        |
| verb_type        | INT        | *controlled* | verb conjugation type (I/II/irreg)  |
| verb_infinitive  | BOOLEAN    |              |                                     |
| verb_mood        | INT        | *controlled* |                                     |
| verb_trans_refl  | INT        | *controlled* | transitivity, reflexivity of a verb |
| conj_person      | INT        | *controlled* | x-person verb conjugation           |
| part_type        | INT        | *controlled* | type of participle                  |
| part_voice       | INT        | *controlled* | voice of participle                 |
| part_parent_verb | INT        | <lemmas(id)> | participle's parent (verb) id       |
| subst_case       | INT        | *controlled* | grammatical case                    |
| noun_animacy    | BOOLEAN    |              | animate nouns                       |
| adjv_short       | BOOLEAN    |              | short adjectives                    |
| conj_gender      | INT        | *controlled* | grammatical gender                  |
| gram_number      | INT        | *controlled* | grammatical number                  |
| gram_tense       | INT        |              | past tense                          |
| noun_dimun       | BOOLEAN    |              | dimunitive nouns                    |
| adjv_comp_type   | INT        | *controlled* | adjectival comparative types        |

#### controlled vocab

| property         | value | meaning       |
| ---------------- | ----- | ------------- |
| verb_aspect      | 0     | imperfective  |
|                  | 1     | perfective    |
|                  | 2     | dual          |
| verb_conj_type   | 1     | Type I        |
|                  | 2     | Type II       |
| verb_mood        | 0     | indicative    |
|                  | 1     | imperative    |
| verb_trans_refl  | 0     | transitive    |
|                  | 1     | reflexive     |
|                  | 2     | neither       |
| verb_conj_person | 1     | first         |
|                  | 2     | second        |
|                  | 3     | third         |
| part_type        | 0     | adjectival    |
|                  | 1     | adverbial     |
| part_voice       | 0     | active        |
|                  | 1     | passive       |
| subst_case       | 0     | nominative    |
|                  | 1     | genitive      |
|                  | 2     | accusative    |
|                  | 3     | dative        |
|                  | 4     | instrumental  |
|                  | 5     | prepositional |
|                  | 6     | vocative      |
|                  | 7     | locative      |
|                  | 8     | partitive     |
| conj_gender      | 0     | masculine     |
|                  | 1     | feminine      |
|                  | 2     | neuter        |
|                  | 3     | dual M/F      |
| gram_number      | 0     | singular      |
|                  | 1     | plural        |
|                  | 2     | dual          |
| adjv_comp_type   | 0     | comparative   |
|                  | 1     | superlative   |

### 03. word_forms

Represents words in context; joins lexicon (real form), lemmas (base form), gram_props (contextual properties of lemma, indicating lexeme)

| name       | type   | constraints          | description |
| ---------- | ------ | -------------------- | ----------- |
| id         | SERIAL | PRIMARY KEY          |             |
| lemma_id   | INT    | NOT NULL lemma(id)   |             |
| lexicon_id | INT    | NOT NULL lexicon(id) |             |
| grammar_id | INT    | NOT NULL grammar(id) |             |

## Sentence Tables

### 04. sent_docs

Sentence source metadata

| name    | type   | constraints | description |
| ------- | ------ | ----------- | ----------- |
| id      | SERIAL | PRIMARY KEY |             |
| author  | TEXT   | NOT NULL    |             |
| date    | DATE   | NOT NULL    |             |
| source  | TEXT   | NOT NULL    |             |
| title   | TEXT   | NOT NULL    |             |
| comment | TEXT   | NOT NULL    |             |

### 05. sentences

text table for sentences

| name       | type   | constraints          | description |
| ---------- | ------ | -------------------- | ----------- |
| id         | SERIAL | PRIMARY KEY          |             |
| sent_text  | TEXT   | NOT NULL             |             |
| lexicon_id | INT    | NOT NULL lexicon(id) |             |
| grammar_id | INT    | NOT NULL grammar(id) |             |

### 06. sent_doc_sents

Sentences in sentence documents

| name        | type | constraints            | description |
| ----------- | ---- | ---------------------- | ----------- |
| sent_doc_id | INT  | NOT NULL sent_docs(id) |             |
| sent_id     | INT  | NOT NULL sentences(id) |             |

### 07. sentence_lexemes

join table for sentence lexicon

| name       | type | constraints            | description |
| ---------- | ---- | ---------------------- | ----------- |
| sent_id    | INT  | NOT NULL sent_docs(id) |             |
| lexicon_id | INT  | NOT NULL lexemes(id)   |             |

## Paragraph Tables

TBA

### 08. definitions

Definitions of lemmas

| name     | type   | constraints     | description                                     |
| -------- | ------ | --------------- | ----------------------------------------------- |
| id       | SERIAL | PRIMARY KEY     |                                                 |
| def_text | TEXT   | NOT NULL UNIQUE | text of definition given for one or more lemmas |

### 09. def_examples

Example sentences from definitions

| name      | type   | constraints     | description                                 |
| --------- | ------ | --------------- | ------------------------------------------- |
| id        | SERIAL | PRIMARY KEY     |                                             |
| sent_text | TEXT   | NOT NULL UNIQUE | text of sentence associated with definition |

### 10. def_sents

Joins definitions, definition_sentences

| name    | type | constraints               | description |
| ------- | ---- | ------------------------- | ----------- |
| def_id  | INT  | NOT NULL definitions(id)  |             |
| sent_id | INT  | NOT NULL def_examples(id) |             |

### 11. lemma_defs

Joins lemmas, definitions

| name     | type | constraints          | description |
| -------- | ---- | -------------------- | ----------- |
| lemma_id | INT  | NOT NULL PRIMARY KEY |             |
| def_id   | INT  | NOT NULL PRIMARY KEY |             |

### 12. verb_pairs

Joins 2 lemmas to create an aspectual verb pair

| name            | type | constraints          | description |
| --------------- | ---- | -------------------- | ----------- |
| imperfective_id | INT  | NOT NULL PRIMARY KEY |             |
| perfective_id   | INT  | NOT NULL PRIMARY KEY |             |

## Vocab Organization

### 13. modules

List of textbook modules

| name        | type        | constraints | description |
| ----------- | ----------- | ----------- | ----------- |
| id          | SERIAL      | PRIMARY KEY |             |
| module_name | VARCHAR(10) | NOT NULL    |             |

### 14. lessons_lists

List of lessons and custom vocab lists

| name         | type        | constraints | description |
| ------------ | ----------- | ----------- | ----------- |
| id           | SERIAL      | PRIMARY KEY |             |
| leslist_name | VARCHAR(50) | NOT NULL    |             |
| topic        | TEXT        |             |             |

### 15. lesslists_in_modules

Represents lessons in modules; joins lessons, modules

| name      | type | constraints                            | description |
| --------- | ---- | -------------------------------------- | ----------- |
| lesson_id | INT  | NOT NULL lessons_lists(id) PRIMARY KEY |             |
| module_id | INT  | NOT NULL modules(id) PRIMARY KEY       |             |

### 16. words_in_leslists

Represents words in lessons and custom word lists; joins lemmas, lesson_lists

| name     | type        | constraints | description |
| -------- | ----------- | ----------- | ----------- |
| id       | SERIAL      | PRIMARY KEY |             |
| lem_text | VARCHAR(50) | PRIMARY KEY |             |

## users

### 17. users

Users

| name     | type        | constraints | description |
| -------- | ----------- | ----------- | ----------- |
| id       | SERIAL      | PRIMARY KEY |             |
| lem_text | VARCHAR(50) | PRIMARY KEY |             |

### 18. user_groups

User groups

| name  | type        | constraints | description |
| ----- | ----------- | ----------- | ----------- |
| id    | SERIAL      | PRIMARY KEY |             |
| group | VARCHAR(50) | PRIMARY KEY |             |

### 19. users_in_groups

Users in groups; joins users, groups

| name     | type | constraints                          | description |
| -------- | ---- | ------------------------------------ | ----------- |
| group_id | INT  | NOT NULL user_groups(id) PRIMARY KEY |             |
| user_id  | INT  | NOT NULL users(id) PRIMARY KEY       |             |

## questions & answers

### 20. questions

student-generated questions

### 21. question_sessions

students' sessions composed of questions

### 22. student_responses

student responses to questions

### 23. student_decisions

student decision tracking for, e.g., popular topics or overlooked vocab

## skills

### 24. skills

skills for BKT

#### table

#### controlled vocab

### 25. skills_in_questions

joins skills, questions

### 26. student_skill_mastery

measurements of students' masteries of skills

## experiments

### 27. user_experiments

A/B testing
