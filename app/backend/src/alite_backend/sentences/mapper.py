#
from typing import Dict, Any
from enum import Enum
from alite_backend.db import models, schemas

corpus_location = "./raw/SynTagRus2022/"
bodyTextDf_loc = "./data/bodyTextDf.json"
bodyLibDf_loc = "./data/bodyLibDf.json"
infDict_loc = "./data/infDict.json"
infDictDf_loc = "./data/infDictDf.json"

feat_def_dict = {
    "S": ("pos", models.EnumPartOfSpeech.NOUN),
    "A": ("pos", models.EnumPartOfSpeech.ADJECTIVE),
    "V": ("pos", models.EnumPartOfSpeech.VERB),
    "ADV": ("pos", models.EnumPartOfSpeech.ADVERB),
    "NUM": ("pos", models.EnumPartOfSpeech.NUMERAL),
    "PR": ("pos", models.EnumPartOfSpeech.PREPOSITION),
    "COM": ("pos", models.EnumPartOfSpeech.COM),
    "CONJ": ("pos", models.EnumPartOfSpeech.CONJUNCTION),
    "P": ("pos", models.EnumPartOfSpeech.PRONOUN),
    "PART": ("pos", models.EnumPartOfSpeech.PARTICLE),
    "INTJ": ("pos", models.EnumPartOfSpeech.INTERJECTION),
    "NID": ("pos", models.EnumPartOfSpeech.UNKNOWN),
    "ОД": ("noun_animacy", True),
    "НЕОД": ("noun_animacy", False),
    "МУЖ": ("gram_gender", models.EnumGramGender.MASCULINE),
    "ЖЕН": ("gram_gender", models.EnumGramGender.FEMININE),
    "СРЕД": ("gram_gender", models.EnumGramGender.NEUTER),
    "ЕД": ("gram_number", models.EnumGramNum.SINGULAR),
    "МН": ("gram_number", models.EnumGramNum.PLURAL),
    "ИМ": ("subst_case", models.EnumSubstCase.NOMINATIVE),
    "РОД": ("subst_case", models.EnumSubstCase.GENITIVE),
    "ПАРТ": ("subst_case", models.EnumSubstCase.PARTITIVE),
    "ДАТ": ("subst_case", models.EnumSubstCase.DATIVE),
    "ВИН": ("subst_case", models.EnumSubstCase.ACCUSATIVE),
    "ТВОР": ("subst_case", models.EnumSubstCase.INSTRUMENTAL),
    "ПР": ("subst_case", models.EnumSubstCase.PREPOSITIONAL),
    "МЕСТН": ("subst_case", models.EnumSubstCase.LOCATIVE),
    "СРАВ": ("alt_adjv_type", models.EnumAltAdjvType.COMPARATIVE),
    "ПРЕВ": ("alt_adjv_type", models.EnumAltAdjvType.SUPERLATIVE),
    "КР": ("alt_adjv_type", models.EnumAltAdjvType.SHORT),
    "ИНФ": ("verb_infinitive", True),
    "ИЗЪЯВ": ("verb_mood", models.EnumVerbMood.INDICATIVE),
    "ПОВ": ("verb_mood", models.EnumVerbMood.IMPERATIVE),
    "НЕСОВ": ("verb_aspect", models.EnumVerbAspect.IMPERFECTVE),
    "СОВ": ("verb_aspect", models.EnumVerbAspect.PERFECTIVE),
    "1-Л": ("verb_conj_person", models.EnumConjPerson.FIRST),
    "2-Л": ("verb_conj_person", models.EnumConjPerson.SECOND),
    "3-Л": ("verb_conj_person", models.EnumConjPerson.THIRD),
    # "СТРАД": ("verb_trans_refl", models.EnumVerbTransRefl.REFLEXIVE),
    "ПРИЧ": ("part_type", models.EnumPartType.ADJECTIVAL),
    "ДЕЕПР": ("part_type", models.EnumPartType.ADVERBIAL),
    # "other": ["СЛ", "СМЯГ"],
}

def parse_features(feat_string: str) -> Dict[str, Any]:
    """
    Parses a space-separated feature string into a dictionary based on feat_def_dict.
    O(N) complexity where N is the number of traits per word.
    """
    if not feat_string:
        return {}
        
    parsed_traits = {}
    for code in feat_string.split():
        mapping = feat_def_dict.get(code)
        if mapping:
            col_name, val = mapping
            # Use .value if using Enums so it's DB-ready (e.g., "NOUN" instead of <POS.NOUN>)
            parsed_traits[col_name] = val.value if isinstance(val, Enum) else val
            
    return parsed_traits