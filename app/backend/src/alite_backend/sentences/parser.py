#
import os
import re
import xml.etree.ElementTree as ET
from typing import Dict, Any, Tuple, List
import dateparser
from alite_backend.db import models, schemas
from alite_backend.sentences.mapper import feat_def_dict, parse_features

corpus_location = "./raw/SynTagRus2022/"
bodyTextDf_loc = "./data/bodyTextDf.json"
bodyLibDf_loc = "./data/bodyLibDf.json"
infDict_loc = "./data/infDict.json"
infDictDf_loc = "./data/infDictDf.json"


def list_files_recursive(
    path=".", ff=None, file_ext=".tgt", re_pattern=False, sort=False
):

    # instantiate list for all files
    file_list = []

    def filter_files(path):
        for root, dirs, files in os.walk(path):
            # Remove unwanted dirs in-place
            dirs[:] = [
                d for d in dirs if not d.startswith(".") and d != ".ipynb_checkpoints"
            ]

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


# def parseW_optimized(file_list, feat_dict):
#     """
#     Parses a list of XML files into DataFrames in a more optimized way.

#     Args:
#         file_list (list): A list of file paths to the XML files.
#         feat_dict (dict): A dictionary mapping feature categories to their codes.

#     Returns:
#         tuple: A tuple containing (parsed_inf_dict, parsedBodyLibDf, parsedBodyTextDf).
#     """
#     # --- 1. Pre-computation (Moved outside the loop) ---
#     # Invert the dictionary once before the loop begins.
#     code_to_category = {
#         code: category for category, codes in feat_dict.items() for code in codes
#     }

#     # Helper function is also defined once.
#     def assign_codes(code_list):
#         if not isinstance(code_list, list):
#             return {cat: None for cat in feat_dict.keys()}

#         result = {cat: [] for cat in feat_dict.keys()}
#         for code in code_list:
#             category = code_to_category.get(code)
#             if category:
#                 result[category].append(code)
#         return {cat: ' '.join(codes) if codes else None for cat, codes in result.items()}

#     # --- 2. Process files and collect DataFrames in a list ---
#     all_body_dfs = []
#     parsed_inf_dict = {}

#     print(f"Processing {len(file_list)} files...")
#     for doc_id, file in enumerate(file_list):
#         # Process metadata
#         parsed_inf = pd.read_xml(file, xpath="/text/inf").T[0].to_dict()
#         parsed_inf_dict[doc_id] = parsed_inf

#         # Process main content from files like A_on_myatezhnyi.tgt
#         wDf = pd.read_xml(file, xpath="/text/body/S/W")

#         # --- 3. Vectorized and Chained Operations ---
#         wDf.columns = wDf.columns.str.lower()
#         wDf = wDf.rename(columns={'id': 'word_id'})

#         # Calculate sentence IDs more efficiently using cumsum()
#         sent_starts = wDf['word_id'] == 1
#         wDf['sent_id'] = sent_starts.cumsum()

#         wDf['lemma'] = wDf['lemma'].str.lower()

#         # Process the 'feat' column
#         if 'feat' in wDf.columns:
#             new_cols_df = wDf['feat'].str.split().apply(assign_codes).apply(pd.Series)
#             wDf = pd.concat([wDf, new_cols_df], axis=1)
#             wDf = wDf.drop(columns=['feat'])

#         wDf['doc_id'] = doc_id
#         all_body_dfs.append(wDf)

#     # --- 4. Single Concatenation After the Loop ---
#     if not all_body_dfs:
#         return {}, pd.DataFrame(), pd.DataFrame()

#     parsedBodyDf = pd.concat(all_body_dfs, ignore_index=True)
#     parsedBodyDf = parsedBodyDf.reset_index().rename(columns={'index': 'doc_tok_id'})

#     # --- 5. Final DataFrame Slicing ---
#     lib_cols = [
#         'doc_id', 'sent_id', 'word_id', 'doc_tok_id', 'dom', 'link', 'lemma',
#         'ksname', 'nodetype', 'extracomm', 'status'
#     ]
#     text_cols = [
#         'doc_id', 'doc_tok_id', 'w', 'pos', 'animacy', 'gender', 'number',
#         'case', 'adjective_level', 'shortness', 'verb_rep', 'mood',
#         'aspect', 'person', 'passive', 'word_formation', 'mod_comparative'
#     ]

#     # Filter columns to only those that exist to avoid KeyErrors
#     # parsedBodyLibDf = parsedBodyDf[[col for col in lib_cols if col in parsedBodyDf.columns]]
#     # parsedBodyTextDf = parsedBodyDf[[col for col in text_cols if col in parsedBodyDf.columns]]

#     return parsed_inf_dict, parsedBodyDf

# file_list = list_files_recursive(corpus_location, ff=True, sort=True)

# parsedInfDict, parsedBodyDf = parseW_optimized(file_list, feat_dict)


def normalize_syntagrus_date(raw_date_str: str):
    """
    Parses fuzzy Russian dates into standard Python datetime objects.
    """
    if not raw_date_str:
        return None

    # languages=['ru'] forces the parser to look for Russian month names.
    parsed_date = dateparser.parse(raw_date_str, languages=["ru"])

    return parsed_date


def parse_tgt_file(
    file_path: str,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Parses a SynTagRus .tgt file into native Python dictionaries.
    Bypasses Pandas entirely for optimal ETL performance into SQL databases.

    Returns:
        doc_data: Dict containing document-level metadata.
        sentences_data: List of Dicts containing sentence data.
        tokens_data: List of Dicts containing word/token data.
    """
    # initialize the XML parser
    tree = ET.parse(file_path)
    root = tree.getroot()

    # extract document metadata (<inf> tag)
    inf_node = root.find("./inf")

    # safely extract text using findtext. defaults to None if the tag is missing.
    title = inf_node.findtext("title")  # type: ignore
    author = inf_node.findtext("author")  # type: ignore
    source = inf_node.findtext("source")  # type: ignore
    date_str = inf_node.findtext("date")  # type: ignore

    # use dateparser to normalize the date
    clean_date = normalize_syntagrus_date(date_str)  # type: ignore

    date = clean_date or date_str

    # collate document data
    doc_data = {"title": title, "author": author, "source": source, "date": date}

    # extract sentences and tokens
    sentences_data = []
    tokens_data = []

    # iterate over all <S> (sentence) elements
    for s_node in root.findall(".//S"):
        # SynTagRus sequential ID
        sent_idx = int(s_node.get("ID", 0))

        # .itertext() grabs all raw text recursively, bypassing the <W> XML nodes
        # This gives us the clean, readable sentence.
        raw_text = "".join(s_node.itertext()).replace("\n", "").strip()

        sentences_data.append(
            {
                # document_id will be injected in the load script after Doc insertion
                "sent_idx": sent_idx,
                "raw_text": raw_text,
            }
        )

        # non-lexical symbols (punctuation) extraction
        punc_before = (s_node.text or "").strip()

        # iterate over all <W> (word) elements within the current sentence
        for w_node in s_node.findall("W"):
            # SynTagRus dependency trees map the root word as '_root'.
            # a postgresql integer column requires an actual integer or NULL.
            if w_node is not None:
                raw_dom = w_node.get("DOM")
                head_index = int(raw_dom) if raw_dom and raw_dom != "_root" else None
                lexeme = w_node.text.strip() if w_node.text else None
                if not lexeme:
                    continue
                punc_after = w_node.tail.strip() if w_node.tail else None

                # apply transformation mapping to the FEAT string
                features = parse_features(w_node.get("FEAT", ""))

                tokens_data.append(
                    {
                        "sent_idx": sent_idx,
                        "token_idx": int(w_node.get("ID", 0)),
                        "lex_raw": lexeme,
                        "lem_raw": w_node.get("LEMMA"),
                        "head_idx": head_index,
                        "dep_rel": w_node.get("LINK"),
                        "semantic_tag": w_node.get("KSNAME"),
                        "is_uppercase": lexeme[0].isupper(),
                        "punctuation_before": punc_before or None,
                        "punctuation_after": punc_after or None,
                        "features": features,
                    }
                )

                punc_before = None

    return doc_data, sentences_data, tokens_data
