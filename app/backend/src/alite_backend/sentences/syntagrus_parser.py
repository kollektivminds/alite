import os
import pandas as pd
import re
import json


corpus_location = './raw/SynTagRus2022'
bodyTextDf_loc = './data/bodyTextDf.json'
bodyLibDf_loc = './data/bodyLibDf.json'
infDict_loc = './data/infDict.json'
infDictDf_loc = './data/infDictDf.json'

feat_def_dict = {
    "pos" : {
        "S": 2, # noun
        "A": 0, # adjective
        "V": 11, # verb
        "ADV": 1, # adverb
        "NUM": 6, # number
        "PR": 9, # preposition
        "COM": 2, # TODO: figure out what this means
        "CONJ": 3, # conjunction
        "P": 5, # pronoun
        "PART": 8, # particle
        "INTJ": 4, # interjection
        "NID": 12,  # no ID
    },
    "subst_animacy" : {
        "ОД": True,
        "НЕОД": False
        },
    "gram_gender" : {
        "МУЖ": 0,
        "ЖЕН": 1,
        "СРЕД": 2
        },
    "gram_number" : {
        "ЕД": 0,
        "МН": 1
        },
    "subst_case" : {
        "ИМ": 0,
        "РОД": 1,
        "ПАРТ": 8,
        "ДАТ": 3,
        "ВИН": 2,
        "ТВОР": 4,
        "ПР": 5,
        "МЕСТН": 7
        },
    "adjv_comp_type" : ["СРАВ", "ПРЕВ"],
    "adjv_short" : ["КР"],
    "verb_infinitive" : {
        "ИНФ": True
    },
    "verb_mood" : {
        "ИЗЪЯВ": 0,
        "ПОВ": 1
    },
    "verb_aspect" : {
        "НЕСОВ": 0,
        "СОВ": 1
        },
    "verb_conj_person" : {
        "1-Л": 1,
        "2-Л": 2,
        "3-Л": 3
        },
    "other" : ["СТРАД", "СЛ", "ПРИЧ", "ДЕЕПР", "СМЯГ"]
    }

def list_files_recursive(path='.', ff=None, file_ext=".tgt", re_pattern=False, sort=False):
    """list_files_recursive helper function to get all files recursively

    Args:
        path (str, optional): _description_. Defaults to '.'.
        ff (_type_, optional): _description_. Defaults to None.
        file_ext (str, optional): _description_. Defaults to ".tgt".
        re_pattern (bool, optional): _description_. Defaults to False.
        sort (bool, optional): _description_. Defaults to False.

    Returns:
        list: a recursive list of files
    """
    # instantiate list for all files
    file_list = []
    
    def filter_files(path):
        for root, dirs, files in os.walk(path):
            # Remove unwanted dirs in-place
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '.ipynb_checkpoints']
        
            for f in files:
                if f.endswith(file_ext) and not f.startswith("."):
                    full_path = os.path.join(root, f)
                    file_list.append(full_path)
        
    if ff:
        filter_files(path)
    else:
        # for loop through the dirs
        for root, dirs, files in os.walk(path):
            for file in files:
                # check for existence of RE pattern to be applied
                if re_pattern != None:
                    f = re.compile(re_pattern)
                    if f.search(file):
                        file_list.append(os.path.join(root, file))
                else:
                    file_list.append(os.path.join(root, file))

    if sort:
        file_list.sort()
    
    return file_list

# TODO: replace with new feat_def_dict
def parseW_optimized(file_list, feat_dict):
    """
    Parses a list of XML files into DataFrames in a more optimized way.

    Args:
        file_list (list): A list of file paths to the XML files.
        feat_dict (dict): A dictionary mapping feature categories to their codes.

    Returns:
        tuple: A tuple containing (parsed_inf_dict, parsedBodyLibDf, parsedBodyTextDf).
    """
    # --- 1. Pre-computation (Moved outside the loop) ---
    # Invert the dictionary once before the loop begins.
    code_to_category = {
        code: category for category, codes in feat_dict.items() for code in codes
    }

    # Helper function is also defined once.
    def assign_codes(code_list):
        if not isinstance(code_list, list):
            return {cat: None for cat in feat_dict.keys()}
        
        result = {cat: [] for cat in feat_dict.keys()}
        for code in code_list:
            category = code_to_category.get(code)
            if category:
                result[category].append(code)
        return {cat: ' '.join(codes) if codes else None for cat, codes in result.items()}

    # --- 2. Process files and collect DataFrames in a list ---
    all_body_dfs = []
    parsed_inf_dict = {}

    print(f"Processing {len(file_list)} files...")
    for doc_id, file in enumerate(file_list):
        # Process metadata
        parsed_inf = pd.read_xml(file, xpath="/text/inf").T[0].to_dict()
        parsed_inf_dict[doc_id] = parsed_inf

        # Process main content from files like A_on_myatezhnyi.tgt
        wDf = pd.read_xml(file, xpath="/text/body/S/W")
        
        # --- 3. Vectorized and Chained Operations ---
        wDf.columns = wDf.columns.str.lower()
        wDf = wDf.rename(columns={'id': 'word_id'})
        
        # Calculate sentence IDs more efficiently using cumsum()
        sent_starts = wDf['word_id'] == 1
        wDf['sent_id'] = sent_starts.cumsum()
        
        wDf['lemma'] = wDf['lemma'].str.lower()

        # Process the 'feat' column
        if 'feat' in wDf.columns:
            new_cols_df = wDf['feat'].str.split().apply(assign_codes).apply(pd.Series)
            wDf = pd.concat([wDf, new_cols_df], axis=1)
            wDf = wDf.drop(columns=['feat'])

        wDf['doc_id'] = doc_id
        all_body_dfs.append(wDf)

    # --- 4. Single Concatenation After the Loop ---
    if not all_body_dfs:
        return {}, pd.DataFrame(), pd.DataFrame()
        
    parsedBodyDf = pd.concat(all_body_dfs, ignore_index=True)
    parsedBodyDf = parsedBodyDf.reset_index().rename(columns={'index': 'doc_tok_id'})

    # --- 5. Final DataFrame Slicing ---
    lib_cols = [
        'doc_id', 'sent_id', 'word_id', 'doc_tok_id', 'dom', 'link', 'lemma',
        'ksname', 'nodetype', 'extracomm', 'status'
    ]
    text_cols = [
        'doc_id', 'doc_tok_id', 'w', 'pos', 'animacy', 'gender', 'number', 
        'case', 'adjective_level', 'shortness', 'verb_rep', 'mood', 
        'aspect', 'person', 'passive', 'word_formation', 'mod_comparative'
    ]
    
    # Filter columns to only those that exist to avoid KeyErrors
    parsedBodyLibDf = parsedBodyDf[[col for col in lib_cols if col in parsedBodyDf.columns]]
    parsedBodyTextDf = parsedBodyDf[[col for col in text_cols if col in parsedBodyDf.columns]]
    
    return parsed_inf_dict, parsedBodyLibDf, parsedBodyTextDf

# make list of files to parse
file_list = list_files_recursive(corpus_location, ff=True, sort=True)

# parse list of files, returning 3 DataFrames with meta, text, and grammar data
parsedInfDict, parsedBodyLibDf, parsedBodyTextDf = parseW_optimized(file_list, feat_dict)
