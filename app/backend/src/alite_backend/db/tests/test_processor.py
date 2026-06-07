import pytest
from pydantic import ValidationError
from alite_backend.words.process import ReturnedLemmaProcessor
from alite_backend.db import schemas, models


@pytest.fixture
def processor():
    return ReturnedLemmaProcessor()


def test_debug_specific_problem_words():
    """
    Justification: By hardcoding the exact edge cases that are currently causing
    VARCHAR or regex truncation failures, we bypass the pipeline overhead and
    can run this atomic test loop on repeat via the VS Code testing tab.
    """
    processor = ReturnedLemmaProcessor()

    # 1. ARRANGE: Input the exact raw data snippet that crashes the parser.
    # Mimic a broken payload layout where your regex gets stuck or truncates.
    ubiitsa_data = {
        "word": "убийца",
        "entries": [
            {
                "language": {"code": "ru", "name": "Russian"},
                "partOfSpeech": "noun",
                "pronunciations": [{"type": "ipa", "text": "[ʊˈbʲijt͡sə]", "tags": []}],
                "forms": [
                    {
                        "word": "уби́йца m anim or f anim by sense",
                        "tags": ["canonical"],
                    },
                    {"word": "ubíjca", "tags": ["romanization"]},
                    {"word": "уби́йцы", "tags": ["genitive"]},
                    {"word": "уби́йцы", "tags": ["nominative", "plural"]},
                    {"word": "уби́йц", "tags": ["genitive", "plural"]},
                    {"word": "no-table-tags", "tags": ["table-tags"]},
                    {"word": "ru-noun-table", "tags": ["inflection-template"]},
                    {"word": "ц-stem", "tags": ["class"]},
                    {"word": "accent-a", "tags": ["class"]},
                    {"word": "уби́йца", "tags": ["nominative", "singular"]},
                    {"word": "уби́йцы", "tags": ["nominative", "plural"]},
                    {"word": "уби́йцы", "tags": ["genitive", "singular"]},
                    {"word": "уби́йц", "tags": ["genitive", "plural"]},
                    {"word": "уби́йце", "tags": ["dative", "singular"]},
                    {"word": "уби́йцам", "tags": ["dative", "plural"]},
                    {"word": "уби́йцу", "tags": ["accusative", "singular"]},
                    {"word": "уби́йц", "tags": ["accusative", "plural"]},
                    {"word": "уби́йцей", "tags": ["instrumental", "singular"]},
                    {"word": "уби́йцею", "tags": ["instrumental", "singular"]},
                    {"word": "уби́йцами", "tags": ["instrumental", "plural"]},
                    {"word": "уби́йце", "tags": ["prepositional", "singular"]},
                    {"word": "уби́йцах", "tags": ["plural", "prepositional"]},
                    {"word": "убі́йца", "tags": ["alternative"]},
                ],
                "senses": [
                    {
                        "definition": "murderer",
                        "tags": [],
                        "examples": [],
                        "quotes": [],
                        "synonyms": [],
                        "antonyms": [],
                        "subsenses": [],
                    },
                    {
                        "definition": "assassin",
                        "tags": [],
                        "examples": ["наёмный уби́йца"],
                        "quotes": [],
                        "synonyms": [],
                        "antonyms": [],
                        "subsenses": [],
                    },
                ],
                "synonyms": [],
                "antonyms": [],
            }
        ],
        "source": {
            "url": "https://en.wiktionary.org/wiki/убийца",
            "license": {
                "name": "CC BY-SA 4.0",
                "url": "https://creativecommons.org/licenses/by-sa/4.0/",
            },
        },
    }

    bezhat_data = {
        "word": "бежать",
        "entries": [
            {
                "language": {"code": "ru", "name": "Russian"},
                "partOfSpeech": "verb",
                "pronunciations": [{"type": "ipa", "text": "[bʲɪˈʐatʲ]", "tags": []}],
                "forms": [
                    {
                        "word": "бежа́ть",
                        "tags": ["canonical", "imperfective", "perfective"],
                    },
                    {"word": "bežátʹ", "tags": ["romanization"]},
                    {"word": "побежа́ть", "tags": ["perfective"]},
                    {"word": "imperfective intransitive", "tags": ["table-tags"]},
                    {"word": "ru-conj", "tags": ["inflection-template"]},
                    {"word": "5b imperfective intransitive", "tags": ["class"]},
                    {"word": "бежа́ть", "tags": ["imperfective", "infinitive"]},
                    {"word": "бегу́щий", "tags": ["active", "participle", "present"]},
                    {"word": "бежа́вший", "tags": ["active", "participle", "past"]},
                    {"word": "-", "tags": ["participle", "passive", "present"]},
                    {"word": "-", "tags": ["participle", "passive", "past"]},
                    {"word": "-", "tags": ["adverbial", "participle", "present"]},
                    {"word": "бежа́в", "tags": ["adverbial", "participle", "past"]},
                    {"word": "бежа́вши", "tags": ["adverbial", "participle", "past"]},
                    {"word": "бегу́", "tags": ["first-person", "present", "singular"]},
                    {
                        "word": "бу́ду бежа́ть",
                        "tags": ["first-person", "future", "singular"],
                    },
                    {
                        "word": "бежи́шь",
                        "tags": ["present", "second-person", "singular"],
                    },
                    {
                        "word": "бу́дешь бежа́ть",
                        "tags": ["future", "second-person", "singular"],
                    },
                    {"word": "бежи́т", "tags": ["present", "singular", "third-person"]},
                    {
                        "word": "бу́дет бежа́ть",
                        "tags": ["future", "singular", "third-person"],
                    },
                    {"word": "бежи́м", "tags": ["first-person", "plural", "present"]},
                    {
                        "word": "бу́дем бежа́ть",
                        "tags": ["first-person", "future", "plural"],
                    },
                    {"word": "бежи́те", "tags": ["plural", "present", "second-person"]},
                    {
                        "word": "бу́дете бежа́ть",
                        "tags": ["future", "plural", "second-person"],
                    },
                    {"word": "бегу́т", "tags": ["plural", "present", "third-person"]},
                    {
                        "word": "бу́дут бежа́ть",
                        "tags": ["future", "plural", "third-person"],
                    },
                    {
                        "word": "беги́",
                        "tags": ["imperative", "second-person", "singular"],
                    },
                    {
                        "word": "беги́те",
                        "tags": ["imperative", "plural", "second-person"],
                    },
                    {"word": "бежа́л", "tags": ["masculine", "past", "singular"]},
                    {"word": "бежа́ли", "tags": ["masculine", "past", "plural"]},
                    {"word": "бежа́ла", "tags": ["feminine", "past", "singular"]},
                    {"word": "бежа́ли", "tags": ["feminine", "past", "plural"]},
                    {"word": "бежа́ло", "tags": ["neuter", "past", "singular"]},
                    {"word": "бежа́ли", "tags": ["neuter", "past", "plural"]},
                    {"word": "intransitive perfective", "tags": ["table-tags"]},
                    {"word": "ru-conj", "tags": ["inflection-template"]},
                    {"word": "5b perfective intransitive", "tags": ["class"]},
                    {"word": "бежа́ть", "tags": ["infinitive", "perfective"]},
                    {"word": "-", "tags": ["active", "participle", "present"]},
                    {"word": "бежа́вший", "tags": ["active", "participle", "past"]},
                    {"word": "-", "tags": ["participle", "passive", "present"]},
                    {"word": "-", "tags": ["participle", "passive", "past"]},
                    {"word": "-", "tags": ["adverbial", "participle", "present"]},
                    {"word": "бежа́в", "tags": ["adverbial", "participle", "past"]},
                    {"word": "бежа́вши", "tags": ["adverbial", "participle", "past"]},
                    {"word": "-", "tags": ["first-person", "present", "singular"]},
                    {"word": "бегу́", "tags": ["first-person", "future", "singular"]},
                    {"word": "-", "tags": ["present", "second-person", "singular"]},
                    {
                        "word": "бежи́шь",
                        "tags": ["future", "second-person", "singular"],
                    },
                    {"word": "-", "tags": ["present", "singular", "third-person"]},
                    {"word": "бежи́т", "tags": ["future", "singular", "third-person"]},
                    {"word": "-", "tags": ["first-person", "plural", "present"]},
                    {"word": "бежи́м", "tags": ["first-person", "future", "plural"]},
                    {"word": "-", "tags": ["plural", "present", "second-person"]},
                    {"word": "бежи́те", "tags": ["future", "plural", "second-person"]},
                    {"word": "-", "tags": ["plural", "present", "third-person"]},
                    {"word": "бегу́т", "tags": ["future", "plural", "third-person"]},
                    {
                        "word": "беги́",
                        "tags": ["imperative", "second-person", "singular"],
                    },
                    {
                        "word": "беги́те",
                        "tags": ["imperative", "plural", "second-person"],
                    },
                    {"word": "бежа́л", "tags": ["masculine", "past", "singular"]},
                    {"word": "бежа́ли", "tags": ["masculine", "past", "plural"]},
                    {"word": "бежа́ла", "tags": ["feminine", "past", "singular"]},
                    {"word": "бежа́ли", "tags": ["feminine", "past", "plural"]},
                    {"word": "бежа́ло", "tags": ["neuter", "past", "singular"]},
                    {"word": "бежа́ли", "tags": ["neuter", "past", "plural"]},
                    {"word": "бѣжа́ть", "tags": ["alternative"]},
                ],
                "senses": [
                    {
                        "definition": "(imperfective only) to run, to be running",
                        "tags": ["imperfective"],
                        "examples": [],
                        "quotes": [],
                        "synonyms": [],
                        "antonyms": [],
                        "subsenses": [],
                    },
                    {
                        "definition": "to flee, to be fleeing",
                        "tags": [],
                        "examples": [],
                        "quotes": [],
                        "synonyms": [],
                        "antonyms": [],
                        "subsenses": [],
                    },
                    {
                        "definition": "to avoid, to be avoiding, to shun, to be shunning",
                        "tags": [],
                        "examples": [],
                        "quotes": [],
                        "synonyms": [],
                        "antonyms": [],
                        "subsenses": [],
                    },
                    {
                        "definition": "to run after [with за (za, + instrumental) ‘someone’]",
                        "tags": [],
                        "examples": [],
                        "quotes": [],
                        "synonyms": [],
                        "antonyms": [],
                        "subsenses": [],
                    },
                ],
                "synonyms": [],
                "antonyms": [],
            }
        ],
        "source": {
            "url": "https://en.wiktionary.org/wiki/бежать",
            "license": {
                "name": "CC BY-SA 4.0",
                "url": "https://creativecommons.org/licenses/by-sa/4.0/",
            },
        },
    }

    # 2. ACT: Invoke the method.
    processed_output = processor.process(bezhat_data)

    # breakpoint()
    # 3. ASSERT: Placeholder step to check the schema output shape
    assert processed_output is not None


def test_processor_valid_data(processor):
    """
    ARRANGE: Provide a known, valid dictionary that mimics the FDAPI output.
    """
    ubiitsa_data = {
        "word": "убийца",
        "entries": [
            {
                "language": {"code": "ru", "name": "Russian"},
                "partOfSpeech": "noun",
                "pronunciations": [{"type": "ipa", "text": "[ʊˈbʲijt͡sə]", "tags": []}],
                "forms": [
                    {
                        "word": "уби́йца m anim or f anim by sense",
                        "tags": ["canonical"],
                    },
                    {"word": "ubíjca", "tags": ["romanization"]},
                    {"word": "уби́йцы", "tags": ["genitive"]},
                    {"word": "уби́йцы", "tags": ["nominative", "plural"]},
                    {"word": "уби́йц", "tags": ["genitive", "plural"]},
                    {"word": "no-table-tags", "tags": ["table-tags"]},
                    {"word": "ru-noun-table", "tags": ["inflection-template"]},
                    {"word": "ц-stem", "tags": ["class"]},
                    {"word": "accent-a", "tags": ["class"]},
                    {"word": "уби́йца", "tags": ["nominative", "singular"]},
                    {"word": "уби́йцы", "tags": ["nominative", "plural"]},
                    {"word": "уби́йцы", "tags": ["genitive", "singular"]},
                    {"word": "уби́йц", "tags": ["genitive", "plural"]},
                    {"word": "уби́йце", "tags": ["dative", "singular"]},
                    {"word": "уби́йцам", "tags": ["dative", "plural"]},
                    {"word": "уби́йцу", "tags": ["accusative", "singular"]},
                    {"word": "уби́йц", "tags": ["accusative", "plural"]},
                    {"word": "уби́йцей", "tags": ["instrumental", "singular"]},
                    {"word": "уби́йцею", "tags": ["instrumental", "singular"]},
                    {"word": "уби́йцами", "tags": ["instrumental", "plural"]},
                    {"word": "уби́йце", "tags": ["prepositional", "singular"]},
                    {"word": "уби́йцах", "tags": ["plural", "prepositional"]},
                    {"word": "убі́йца", "tags": ["alternative"]},
                ],
                "senses": [
                    {
                        "definition": "murderer",
                        "tags": [],
                        "examples": [],
                        "quotes": [],
                        "synonyms": [],
                        "antonyms": [],
                        "subsenses": [],
                    },
                    {
                        "definition": "assassin",
                        "tags": [],
                        "examples": ["наёмный уби́йца"],
                        "quotes": [],
                        "synonyms": [],
                        "antonyms": [],
                        "subsenses": [],
                    },
                ],
                "synonyms": [],
                "antonyms": [],
            }
        ],
        "source": {
            "url": "https://en.wiktionary.org/wiki/убийца",
            "license": {
                "name": "CC BY-SA 4.0",
                "url": "https://creativecommons.org/licenses/by-sa/4.0/",
            },
        },
    }

    bezhat_data = {
        "word": "бежать",
        "entries": [
            {
                "language": {"code": "ru", "name": "Russian"},
                "partOfSpeech": "verb",
                "pronunciations": [{"type": "ipa", "text": "[bʲɪˈʐatʲ]", "tags": []}],
                "forms": [
                    {
                        "word": "бежа́ть",
                        "tags": ["canonical", "imperfective", "perfective"],
                    },
                    {"word": "bežátʹ", "tags": ["romanization"]},
                    {"word": "побежа́ть", "tags": ["perfective"]},
                    {"word": "imperfective intransitive", "tags": ["table-tags"]},
                    {"word": "ru-conj", "tags": ["inflection-template"]},
                    {"word": "5b imperfective intransitive", "tags": ["class"]},
                    {"word": "бежа́ть", "tags": ["imperfective", "infinitive"]},
                    {"word": "бегу́щий", "tags": ["active", "participle", "present"]},
                    {"word": "бежа́вший", "tags": ["active", "participle", "past"]},
                    {"word": "-", "tags": ["participle", "passive", "present"]},
                    {"word": "-", "tags": ["participle", "passive", "past"]},
                    {"word": "-", "tags": ["adverbial", "participle", "present"]},
                    {"word": "бежа́в", "tags": ["adverbial", "participle", "past"]},
                    {"word": "бежа́вши", "tags": ["adverbial", "participle", "past"]},
                    {"word": "бегу́", "tags": ["first-person", "present", "singular"]},
                    {
                        "word": "бу́ду бежа́ть",
                        "tags": ["first-person", "future", "singular"],
                    },
                    {
                        "word": "бежи́шь",
                        "tags": ["present", "second-person", "singular"],
                    },
                    {
                        "word": "бу́дешь бежа́ть",
                        "tags": ["future", "second-person", "singular"],
                    },
                    {"word": "бежи́т", "tags": ["present", "singular", "third-person"]},
                    {
                        "word": "бу́дет бежа́ть",
                        "tags": ["future", "singular", "third-person"],
                    },
                    {"word": "бежи́м", "tags": ["first-person", "plural", "present"]},
                    {
                        "word": "бу́дем бежа́ть",
                        "tags": ["first-person", "future", "plural"],
                    },
                    {"word": "бежи́те", "tags": ["plural", "present", "second-person"]},
                    {
                        "word": "бу́дете бежа́ть",
                        "tags": ["future", "plural", "second-person"],
                    },
                    {"word": "бегу́т", "tags": ["plural", "present", "third-person"]},
                    {
                        "word": "бу́дут бежа́ть",
                        "tags": ["future", "plural", "third-person"],
                    },
                    {
                        "word": "беги́",
                        "tags": ["imperative", "second-person", "singular"],
                    },
                    {
                        "word": "беги́те",
                        "tags": ["imperative", "plural", "second-person"],
                    },
                    {"word": "бежа́л", "tags": ["masculine", "past", "singular"]},
                    {"word": "бежа́ли", "tags": ["masculine", "past", "plural"]},
                    {"word": "бежа́ла", "tags": ["feminine", "past", "singular"]},
                    {"word": "бежа́ли", "tags": ["feminine", "past", "plural"]},
                    {"word": "бежа́ло", "tags": ["neuter", "past", "singular"]},
                    {"word": "бежа́ли", "tags": ["neuter", "past", "plural"]},
                    {"word": "intransitive perfective", "tags": ["table-tags"]},
                    {"word": "ru-conj", "tags": ["inflection-template"]},
                    {"word": "5b perfective intransitive", "tags": ["class"]},
                    {"word": "бежа́ть", "tags": ["infinitive", "perfective"]},
                    {"word": "-", "tags": ["active", "participle", "present"]},
                    {"word": "бежа́вший", "tags": ["active", "participle", "past"]},
                    {"word": "-", "tags": ["participle", "passive", "present"]},
                    {"word": "-", "tags": ["participle", "passive", "past"]},
                    {"word": "-", "tags": ["adverbial", "participle", "present"]},
                    {"word": "бежа́в", "tags": ["adverbial", "participle", "past"]},
                    {"word": "бежа́вши", "tags": ["adverbial", "participle", "past"]},
                    {"word": "-", "tags": ["first-person", "present", "singular"]},
                    {"word": "бегу́", "tags": ["first-person", "future", "singular"]},
                    {"word": "-", "tags": ["present", "second-person", "singular"]},
                    {
                        "word": "бежи́шь",
                        "tags": ["future", "second-person", "singular"],
                    },
                    {"word": "-", "tags": ["present", "singular", "third-person"]},
                    {"word": "бежи́т", "tags": ["future", "singular", "third-person"]},
                    {"word": "-", "tags": ["first-person", "plural", "present"]},
                    {"word": "бежи́м", "tags": ["first-person", "future", "plural"]},
                    {"word": "-", "tags": ["plural", "present", "second-person"]},
                    {"word": "бежи́те", "tags": ["future", "plural", "second-person"]},
                    {"word": "-", "tags": ["plural", "present", "third-person"]},
                    {"word": "бегу́т", "tags": ["future", "plural", "third-person"]},
                    {
                        "word": "беги́",
                        "tags": ["imperative", "second-person", "singular"],
                    },
                    {
                        "word": "беги́те",
                        "tags": ["imperative", "plural", "second-person"],
                    },
                    {"word": "бежа́л", "tags": ["masculine", "past", "singular"]},
                    {"word": "бежа́ли", "tags": ["masculine", "past", "plural"]},
                    {"word": "бежа́ла", "tags": ["feminine", "past", "singular"]},
                    {"word": "бежа́ли", "tags": ["feminine", "past", "plural"]},
                    {"word": "бежа́ло", "tags": ["neuter", "past", "singular"]},
                    {"word": "бежа́ли", "tags": ["neuter", "past", "plural"]},
                    {"word": "бѣжа́ть", "tags": ["alternative"]},
                ],
                "senses": [
                    {
                        "definition": "(imperfective only) to run, to be running",
                        "tags": ["imperfective"],
                        "examples": [],
                        "quotes": [],
                        "synonyms": [],
                        "antonyms": [],
                        "subsenses": [],
                    },
                    {
                        "definition": "to flee, to be fleeing",
                        "tags": [],
                        "examples": [],
                        "quotes": [],
                        "synonyms": [],
                        "antonyms": [],
                        "subsenses": [],
                    },
                    {
                        "definition": "to avoid, to be avoiding, to shun, to be shunning",
                        "tags": [],
                        "examples": [],
                        "quotes": [],
                        "synonyms": [],
                        "antonyms": [],
                        "subsenses": [],
                    },
                    {
                        "definition": "to run after [with за (za, + instrumental) ‘someone’]",
                        "tags": [],
                        "examples": [],
                        "quotes": [],
                        "synonyms": [],
                        "antonyms": [],
                        "subsenses": [],
                    },
                ],
                "synonyms": [],
                "antonyms": [],
            }
        ],
        "source": {
            "url": "https://en.wiktionary.org/wiki/бежать",
            "license": {
                "name": "CC BY-SA 4.0",
                "url": "https://creativecommons.org/licenses/by-sa/4.0/",
            },
        },
    }

    # ACT: Run it through the processor
    result = processor.process(bezhat_data)

    # ASSERT: Check that the output matches Pydantic ProcessedPayload schema
    assert result is not None
    # Because you map string tags to Enums in _sort_entries, verify the mapping worked
    assert result.lemmas[0].pos.value == "verb"
    canon_len = len(result.lemmas[0].lem_canon)
    text_len = len(result.lemmas[0].lem_text)

    assert canon_len == 0 or canon_len == text_len + 1


#    assert result.lemmas[0].noun_gender in [e.value for e in models.EnumGramGender]


def test_processor_raises_validation_error_on_bad_schema(processor):
    """
    If the API changes their schema and stops sending 'word', your app should
    catch it via Pydantic rather than silently corrupting your DB.
    """
    bad_api_data = {"missing_word_key": "oops"}

    # Assert that calling process() raises a Pydantic ValidationError
    with pytest.raises(ValidationError):
        processor.process(bad_api_data)
