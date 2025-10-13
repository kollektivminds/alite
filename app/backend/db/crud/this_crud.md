# CRUD Functions

Which function goes where?

## words (with definitions)

### create

```python
def create_lexeme(lex_text: str) -> int:
    # check if lexeme is clean or not, check if exists
    # if exists: return id; if not: create instance and return id
    return lex_id

def create_lemma(lem_text: str, pos: int) -> int:
    # check if lemma exists
    # if exists: return id; if not: create instance and return id
    return lem_id

def create_gram_form(**kwargs) -> int:
    # check if exists; else: create and return id
    return gram_form_id

def create_word_form(lemma_id: int, lex_id: int, gram_id: int) -> int:
    # check if exists; else: create and return id
    return word_form_id

def create_def(def_text: str) -> int:
    # check if exists; else: create and return id
    return def_id

def create_def_sent(def_sent_text: str) -> int:
    # check if exists; else: create and return id
    return def_sent_id

def create_def_in_sent(def_id: int, sent_id: int) -> int:
    # check if exists; else: create and return id
    return def_in_sent_id

def create_verb_pair(imp_verb_id: int, perf_verb_id: int) -> int:
    # check if exists; else: create and return id
    def verb_pair_id
    
def create_lemma_def(lemma_id: int, def_id: int) -> int:
    # check if exists; else: create and return id
    def lemma_def_id

def create_module(mod_name: str) -> int:
    # check if exists; else: create and return id
    def module_id

def create_lesson_list(lesslist_name: str) -> int:
    # check if exists; else: create and return id
    def lemma_def_id

def create_lesslist_in_module(lesslist_id: int, mod_id: int) -> int:
    # check if exists; else: create and return id
    def lesslist_in_mod_id

def create_word_in_lesslist(lemma_id: int, lesslist_id: int) -> int:
    # check if exists; else: create and return id
    def word_in_lesslist_id
```

### read

```python
def lex_exists(lex_text: str) -> bool:
    # check lex_text against lexicon(lex_text, lex_text_clean)
    return does_lexeme_exist

def lem_exists(lem_text: str) -> bool:
    # check lem_text against lemmas(lem_text)
    return does_lemma_exist

def get_lems_by_form(gram_form: dict) -> list[str]:
    # identify input form, connect to lemma, retrieve lemma
    return list_of_lemmas

def get_lems_by_pos(pos_int: int, pos_str: str) -> list[str]:
    # if pos_int: query lemmas table by pos
    # if pos_str: translate to int and then query
    return list_of_lemmas

def get_gram_from_lex(lex_text: str) -> dict:
    # identify lexeme, identify associated lemma, retrieve gram_props x lemma
    return gram_props

def get_pos_from_lem(lem_id: int, lem_text: str) -> int:
    # query lemma table by lem_id or lem_text, retrieve pos id
    return pos_id

def get_verb_partner(imperf_id: int, perf_id: int) -> dict:
    # query verb_pairs table by provided id, return {aspect, lemma}
    return pair_dict

def get_lem_by_def(def_id: int) -> dict:
    # query lemma_defs table by definition id, return {lemma id, lemma}
    return lem_id

def get_def_by_lem(lem_id: int) -> int:
    # query lemma_defs table by lemma id, return {definition id, definition}
    return lem_id
```

### update

### delete

## word organization

### create

```python
def create_module(mod_name: str) -> int:
    # check if module exists; if exists: return id;
    # if not: create instance and return id
    return mod_id

def create_lesslist(lesslist_name: str) -> int:
    # check if lesson_list exists; if exists: return id;
    # if not: create instance and return id
    return lesslist_id

def create_lesslist_in_mod(ll_id: int, mod_id: str) -> int:
    # check if instance exists; if exists: return id;
    # if not: create instance and return id
    return llinmod_id

def create_word_in_lesslist(word_id: int, ll_id: int) -> int:
    # check if instance exists; if exists: return id;
    # if not: create instance and return id
    return wordinll_id

```

### read

```python
def get_module(mod_id: int, mod_name: str) -> dict:
    # check against modules table; return {id, module_name}
    return

def get_lesslist(ll_id: int, ll_name: str, topic: str) -> dict:
    # check against lesslist table; return {id, lesslist_name, topic}
    return

def get_llsinmods(ll_id: int, mod_name: int) -> dict:
    # check against ll_in_mods table: return lls for mod, mod for ll
    return

def get_lemsinlls(lem_id: int, ll_id: int) -> dict:
    # check against words_in_lls table; return lems for lls, lls for lems
    return

```

### update

### delete

## sentences

### create

```python
def create_sent_doc(author: str, date: str, source: str, title: str, comment: str) -> int:
    # check if exists; return id
    return sent_doc_id
```

### read

### update

### delete

## paragraphs (TBD)

## users

### create

```python
def create_user() -> int:
    #
    return user_id

def create_user_group() -> int:
    #
    return user_group_id

def create_user_in_group() -> int:
    #
    return user_in_group_id
```

### read

```python
def get_user_name() -> str:
    #
    return user_name

def get_group_of_user() -> int:
    #
    return group_of_user
```

### update

### delete
