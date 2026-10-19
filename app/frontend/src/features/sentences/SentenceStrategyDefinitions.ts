// src/features/sentences/SentenceStrategyDefinitions.ts
import { EnumItemFormat } from "../../types";

/**
 * Pedagogical functional groupings for sentence-level strategies.
 * Used for hierarchical UI accordions, telemetry categorization,
 * and cognitive load management in configuration panels.
 */
export type EnumSentenceItemGroup =
  | "Morphosyntax"
  | "Annotation"
  | "Syntax"
  | "Composition";

export interface SentenceStrategyDefinition {
  /** Unique string key matching backend EnumSentItemType */
  id: string;
  /** Human-readable label for instructor/student menus */
  label: string;
  /** SLA measurement rationale and instructional prompt description */
  description: string;
  /** Representative sentence prompt with target masking/tagging */
  stemExample: string;
  /** Expected correct resolution or parse tag */
  keyExample: string;
  /** Acceptable deliverable formats validated against STRATEGY_FORMAT_COMPATIBILITY */
  supportedFormats: readonly EnumItemFormat[];
  /** Categorical grouping */
  group: EnumSentenceItemGroup;
}

// src/features/sentences/SentenceStrategyDefinitions.ts (continued)

export const SentenceStrategyTooltips: readonly SentenceStrategyDefinition[] = [
  // =========================================================================
  // 1. MORPHOSYNTAX IN CONTEXT (CLOZE DRILLS)
  // =========================================================================
  {
    id: "NOUN_MORPH",
    label: "Noun Agreement Cloze",
    description:
      "Select or generate the correctly declined form of a target noun within a complete sentence, guided by case governance, prepositions, and lemma hints.",
    stemExample: "Она читает интересную [...] (книга) в библиотеке.",
    keyExample: "книгу",
    supportedFormats: ["fitb", "mcq"],
    group: "Morphosyntax",
  },
  {
    id: "VERB_MORPH",
    label: "Verb Conjugation Cloze",
    description:
      "Produce or select the finite verb form matching tense, person, number, and mood required by the clausal subject and temporal markers.",
    stemExample: "Вчера студенты весь вечер [...] (писать) курсовую работу.",
    keyExample: "писали",
    supportedFormats: ["fitb", "mcq"],
    group: "Morphosyntax",
  },
  {
    id: "ADJECTIVE_MORPH",
    label: "Adjective Agreement Cloze",
    description:
      "Supply the proper adjectival inflection agreeing in gender, number, and case with the governing noun phrase.",
    stemExample: "Мы долго гуляли по [...] (красивый) парку.",
    keyExample: "красивому",
    supportedFormats: ["fitb", "mcq"],
    group: "Morphosyntax",
  },
  {
    id: "LEXICAL",
    label: "Contextual Lexical Cloze",
    description:
      "Discriminate between semantic peers and collocations to fill a masked sentence slot without explicit lemma cues.",
    stemExample: "Поезд [...] вовремя на первый путь вокзала.",
    keyExample: "прибыл",
    supportedFormats: ["mcq", "fitb"],
    group: "Morphosyntax",
  },

  // =========================================================================
  // 2. METALINGUISTIC ANNOTATION
  // =========================================================================
  {
    id: "NOUN_CASE",
    label: "Sentence Noun Case Identification",
    description:
      "Analyze a highlighted noun in authentic syntax and identify its grammatical case based on prepositional government and valence.",
    stemExample: "Капитан передал приказ [матросам].",
    keyExample: "Dative",
    supportedFormats: ["mcq"],
    group: "Annotation",
  },
  {
    id: "VERB_ASPECT",
    label: "Sentence Verb Aspect Identification",
    description:
      "Determine whether the highlighted verb form in a sentential context conveys perfective (completion/result) or imperfective (process/duration) aspect.",
    stemExample: "Художник долго [рисовал] этот портрет.",
    keyExample: "Imperfective",
    supportedFormats: ["mcq"],
    group: "Annotation",
  },
  {
    id: "DEP_REL",
    label: "Syntactic Role / Dependency Relation",
    description:
      "Identify the grammatical function or dependency relation (e.g., subject, direct object, adverbial modifier) of the highlighted token.",
    stemExample: "Старый профессор медленно читал [лекцию].",
    keyExample: "1-компл (Direct Object)",
    supportedFormats: ["mcq"],
    group: "Annotation",
  },

  // =========================================================================
  // 3. SYNTACTIC DEPENDENCY ARCS
  // =========================================================================
  {
    id: "FIND_HEAD",
    label: "Find Syntactic Governor (Head)",
    description:
      "Locate the syntactic head/governor that directly commands the targeted dependent token in the dependency tree.",
    stemExample: "Студенты внимательно слушали [нового] преподавателя.",
    keyExample: "преподавателя",
    supportedFormats: ["mcq", "fitb"],
    group: "Syntax",
  },
  {
    id: "FIND_SUBJECT",
    label: "Identify Clausal Subject",
    description:
      "Isolate the primary grammatical subject (предик relation) of a complex or inverted clause.",
    stemExample: "Поздним вечером на улице неожиданно зазвучала музыка.",
    keyExample: "музыка",
    supportedFormats: ["mcq", "fitb"],
    group: "Syntax",
  },

  // =========================================================================
  // 4. STRUCTURE & COMPOSITION
  // =========================================================================
  {
    id: "UNSCRAMBLE",
    label: "Sentence Unscrambling",
    description:
      "Reconstruct a coherent sentence from a randomized permutation of tokens, requiring pragmatic and syntactic competence.",
    stemExample: "['парке', 'гуляли', 'Вчера', 'мы', 'в']",
    keyExample: "Вчера мы гуляли в парке.",
    supportedFormats: ["unscramble"],
    group: "Composition",
  },
] as const;

/**
 * Pre-flight verification utility for sentence configuration panels.
 * Asserts that any strategy with count > 0 is supported by at least one
 * format selected in the session context.
 */
export function validateSentenceStrategyFormats(
  typeCounts: Record<string, number>,
  selectedFormats: EnumItemFormat[],
): { isValid: boolean; errors: string[] } {
  const activeFormats = new Set(selectedFormats);
  const errors: string[] = [];

  const strategyMap = new Map<string, readonly EnumItemFormat[]>();
  SentenceStrategyTooltips.forEach((def) => {
    strategyMap.set(def.id, def.supportedFormats);
  });

  Object.entries(typeCounts).forEach(([stratId, count]) => {
    if (count > 0) {
      const supported = strategyMap.get(stratId);
      if (!supported) {
        errors.push(`Unknown sentence strategy: '${stratId}'.`);
        return;
      }

      const hasViableFormat = supported.some((fmt) => activeFormats.has(fmt));
      if (!hasViableFormat) {
        errors.push(
          `Strategy '${stratId}' (${count} item(s)) requires one of [${supported.join(
            ", ",
          )}], but none are selected in the session format filter.`,
        );
      }
    }
  });

  return {
    isValid: errors.length === 0,
    errors,
  };
}

/**
 * Canonical ordering of sentence groups for accordion views.
 */
export const ORDERED_SENTENCE_GROUPS: readonly EnumSentenceItemGroup[] = [
  "Morphosyntax",
  "Annotation",
  "Syntax",
  "Composition",
] as const;
