// sentence strategies
import { EnumItemFormat } from "../../types";

export interface StrategyDefinition {
  id: string;
  labelKey: string;
  descriptionKey: string;
  supportedFormats: EnumItemFormat[];
}

export interface StrategyGroup {
  groupKey: string;
  strategies: StrategyDefinition[];
}

export const SENTENCE_STRATEGY_GROUPS: StrategyGroup[] = [
  {
    groupKey: "sentencesMenu.strategies.gramForms",
    strategies: [
      {
        id: "noun_morph",
        labelKey: "sentencesMenu.strategies.nounMorph",
        descriptionKey: "sentencesMenu.desc_cloze_noun",
        supportedFormats: ["mcq", "fitb"],
      },
      {
        id: "adjective_morph",
        labelKey: "sentencesMenu.strategies.adjectiveMorph",
        descriptionKey: "sentencesMenu.desc_cloze_noun",
        supportedFormats: ["mcq", "fitb"],
      },
      {
        id: "verb_morph",
        labelKey: "sentencesMenu.strategies.verbMorph",
        descriptionKey: "sentencesMenu.desc_cloze_verb",
        supportedFormats: ["mcq", "fitb"],
      },
      {
        id: "lexical",
        labelKey: "sentencesMenu.strategies.lexical",
        descriptionKey: "sentencesMenu.desc_cloze_lex",
        supportedFormats: ["mcq"],
      },
    ],
  },
  {
    groupKey: "exercises.formats.wordOrder",
    strategies: [
      {
        id: "unscramble",
        labelKey: "sentencesMenu.strategies.unscramble",
        descriptionKey: "sentencesMenu.desc_unscramble",
        supportedFormats: ["unscramble"],
      },
    ],
  },
  {
    groupKey: "exercises.formats.syntax",
    strategies: [
      {
        id: "dep_rel",
        labelKey: "sentencesMenu.strategies.depRel",
        descriptionKey: "sentencesMenu.desc_dep_rel",
        supportedFormats: ["mcq"],
      },
      {
        id: "find_head",
        labelKey: "sentencesMenu.strategies.findHead",
        descriptionKey: "sentencesMenu.desc_find_head",
        supportedFormats: ["mcq"],
      },
      {
        id: "find_subject",
        labelKey: "sentencesMenu.strategies.findSubject",
        descriptionKey: "sentencesMenu.desc_find_head",
        supportedFormats: ["mcq"],
      },
    ],
  },
];
