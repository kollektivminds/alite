#!/usr/bin/env python3
"""
sync_locale_keys.py

Authoritative localization synchronization utility for ALITE.
Enforces the English locale as the single source of truth (SSOT).

Operates with CLDR-aware plural transformation:
  - English source: requires paired '_one' and '_other' suffixes.
  - Russian target: expands plural bases to '_one', '_few', and '_many'.
  - camelCase keys: strictly synchronized 1:1.
  - Missing translations: defaulted to key name (value = key).
  - Obsolete target keys: pruned automatically.
"""

import argparse
import json
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

# cldr plural suffix rules by language code
LOCALE_PLURAL_RULES: dict[str, list[str]] = {
    "en": ["one", "other"],
    "ru": ["one", "few", "many"],
}

ALL_PLURAL_SUFFIXES: set[str] = {"one", "few", "many", "other"}


def load_json(file_path: Path) -> dict[str, Any]:
    """Loads a JSON file ensuring UTF-8 decoding."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: dict[str, Any], file_path: Path) -> None:
    """
    Serializes JSON with 2-space indentation, preserving non-ASCII Cyrillic
    characters and appending a POSIX-compliant trailing newline.
    """
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def parse_plural_key(key: str) -> tuple[bool, str, str]:
    """
    Analyzes a key to check if it represents a pluralized i18next key.

    Returns:
        tuple[is_plural, base_name, suffix]
        e.g., 'item_one' -> (True, 'item', 'one')
              'startExercise' -> (False, 'startExercise', '')
    """
    if "_" in key:
        base, suffix = key.rsplit("_", 1)
        if suffix in ALL_PLURAL_SUFFIXES:
            return True, base, suffix
    return False, key, ""


def normalize_source_dict(
    source_dict: dict[str, Any],
    lang: str = "en",
    prefix: str = "",
) -> tuple[dict[str, Any], list[str]]:
    """
    Validates and normalizes the English source dictionary.
    Ensures that any plural base has both '_one' and '_other' entries.

    Returns:
        tuple[normalized_dictionary, list_of_reported_issues]
    """
    required_suffixes = LOCALE_PLURAL_RULES.get(lang, ["one", "other"])
    normalized: dict[str, Any] = {}
    issues: list[str] = []
    processed_bases: set[str] = set()

    for key, val in source_dict.items():
        current_path = f"{prefix}.{key}" if prefix else key

        # recurse into nested dictionary trees
        if isinstance(val, dict):
            sub_norm, sub_issues = normalize_source_dict(
                val, lang=lang, prefix=current_path
            )
            normalized[key] = sub_norm
            issues.extend(sub_issues)
            continue

        # check for pluralization
        is_plural, base, suffix = parse_plural_key(key)

        if not is_plural:
            normalized[key] = val
            continue

        # if base was already handled, skip subsequent encounters
        if base in processed_bases:
            continue
        processed_bases.add(base)

        # ensure both '_one' and '_other' are present in source
        for req_suffix in required_suffixes:
            req_key = f"{base}_{req_suffix}"
            req_path = f"{prefix}.{req_key}" if prefix else req_key

            if req_key in source_dict and not isinstance(source_dict[req_key], dict):
                normalized[req_key] = source_dict[req_key]
            else:
                # Missing required counterpart in English
                normalized[req_key] = req_key
                issues.append(
                    f"English source missing required plural key: '{req_path}' (synthesized as '{req_key}')"
                )

        # detect any rogue suffixes in English (e.g., '_few' mistakenly in en)
        for cand_key in source_dict:
            c_plural, c_base, c_suffix = parse_plural_key(cand_key)
            if c_plural and c_base == base and c_suffix not in required_suffixes:
                cand_path = f"{prefix}.{cand_key}" if prefix else cand_key
                issues.append(
                    f"English source contains non-English plural suffix: '{cand_path}' (pruned)"
                )

    return normalized, issues


def project_to_target(
    source_dict: dict[str, Any],
    target_dict: dict[str, Any],
    target_lang: str = "ru",
    prefix: str = "",
) -> tuple[dict[str, Any], list[str], list[str]]:
    """
    Projects the authoritative English structure onto the target locale.

    Rules applied:
      - Normal camelCase keys: preserved if present; missing added as value=key.
      - Plural bases: expanded to target suffixes (for 'ru': '_one', '_few', '_many').
      - Existing target translations: preserved for valid keys.
      - Extraneous/obsolete keys: omitted from the projected output.

    Returns:
        tuple[projected_dict, missing_keys_added, obsolete_keys_pruned]
    """
    target_suffixes = LOCALE_PLURAL_RULES.get(target_lang, ["one", "few", "many"])
    projected: dict[str, Any] = {}
    missing_added: list[str] = []
    processed_bases: set[str] = set()

    for key, source_val in source_dict.items():
        current_path = f"{prefix}.{key}" if prefix else key

        # nested branch: recurse
        if isinstance(source_val, dict):
            raw_target_sub = target_dict.get(key)
            target_sub = raw_target_sub if isinstance(raw_target_sub, dict) else {}

            sub_proj, sub_missing, _ = project_to_target(
                source_val,
                target_sub,
                target_lang=target_lang,
                prefix=current_path,
            )
            projected[key] = sub_proj
            missing_added.extend(sub_missing)
            continue

        # check for plural category
        is_plural, base, _ = parse_plural_key(key)

        if not is_plural:
            # Standard scalar key (camelCase)
            if key in target_dict and not isinstance(target_dict[key], dict):
                projected[key] = target_dict[key]
            else:
                projected[key] = key
                missing_added.append(current_path)
            continue

        # handle plural group expansion
        if base in processed_bases:
            continue
        processed_bases.add(base)

        # generate target keys for this plural base
        for tgt_suffix in target_suffixes:
            tgt_key = f"{base}_{tgt_suffix}"
            tgt_path = f"{prefix}.{tgt_key}" if prefix else tgt_key

            if tgt_key in target_dict and not isinstance(target_dict[tgt_key], dict):
                # Preserve existing localized translation
                projected[tgt_key] = target_dict[tgt_key]
            else:
                # Key is absent: fallback to key name
                projected[tgt_key] = tgt_key
                missing_added.append(tgt_path)

    # identify obsolete keys in target (present in target but not in projected schema)
    obsolete_pruned = collect_obsolete_paths(target_dict, projected, prefix)

    return projected, missing_added, obsolete_pruned


def collect_obsolete_paths(
    target_dict: dict[str, Any], projected_dict: dict[str, Any], prefix: str = ""
) -> list[str]:
    """Recursively finds all keys in target_dict that were pruned in projected_dict."""
    obsolete: list[str] = []
    for k, v in target_dict.items():
        current_path = f"{prefix}.{k}" if prefix else k
        if k not in projected_dict:
            obsolete.append(current_path)
        elif isinstance(v, dict) and isinstance(projected_dict.get(k), dict):
            obsolete.extend(collect_obsolete_paths(v, projected_dict[k], current_path))
    return obsolete


def detect_locale(file_path: Path, default: str) -> str:
    """Infers the language code from the path structure (e.g., locales/ru/translations.json)."""
    for part in file_path.parts:
        if part in LOCALE_PLURAL_RULES:
            return part
    return default


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Synchronize locale files using English as the authoritative source with CLDR pluralization."
    )
    parser.add_argument(
        "source",
        type=Path,
        nargs="?",
        default=Path("app/frontend/src/locales/en/translations.json"),
        help="Authoritative English source JSON file",
    )
    parser.add_argument(
        "target",
        type=Path,
        nargs="?",
        default=Path("app/frontend/src/locales/ru/translations.json"),
        help="Target locale JSON file to project onto",
    )
    parser.add_argument(
        "--source-lang",
        type=str,
        default=None,
        help="Source language code (defaults to detected or 'en')",
    )
    parser.add_argument(
        "--target-lang",
        type=str,
        default=None,
        help="Target language code (defaults to detected or 'ru')",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Apply modifications: normalize source plural pairs, project onto target, and prune obsolete keys.",
    )

    args = parser.parse_args()

    # 1. File existence validation
    if not args.source.exists():
        print(f"Error: Source file not found: {args.source}")
        sys.exit(1)
    if not args.target.exists():
        print(f"Error: Target file not found: {args.target}")
        sys.exit(1)

    source_lang = args.source_lang or detect_locale(args.source, "en")
    target_lang = args.target_lang or detect_locale(args.target, "ru")

    try:
        raw_source_data = load_json(args.source)
        raw_target_data = load_json(args.target)
    except Exception as err:
        print(f"Failed to parse JSON files: {err}")
        sys.exit(1)

    # 2. Step 1: Normalize source (English) plural pairs
    normalized_source, source_issues = normalize_source_dict(
        raw_source_data, lang=source_lang
    )

    # 3. Step 2: Project normalized source onto target (Russian)
    synced_target, missing_added, obsolete_pruned = project_to_target(
        normalized_source, raw_target_data, target_lang=target_lang
    )

    # 4. Assess synchronization divergence
    has_source_divergence = bool(source_issues)
    has_target_divergence = bool(missing_added or obsolete_pruned)
    is_out_of_sync = (
        has_source_divergence
        or has_target_divergence
        or (raw_target_data != synced_target)
    )

    if is_out_of_sync:
        print(
            f"⚠️ Localization divergence detected between {args.source} ({source_lang}) and {args.target} ({target_lang}):"
        )

        if source_issues:
            print(f"\nEnglish Source Plural Issues ({len(source_issues)}):")
            for issue in source_issues:
                print(f"     • {issue}")

        if missing_added:
            print(
                f"\nMissing in {args.target} ({len(missing_added)} keys - mapped as value=key):"
            )
            for key in sorted(missing_added):
                print(f"     + {key}")

        if obsolete_pruned:
            print(
                f"\nObsolete in {args.target} ({len(obsolete_pruned)} keys - will be pruned):"
            )
            for key in sorted(obsolete_pruned):
                print(f"     - {key}")

        if args.fix:
            print(f"\nApplying authoritative sync...")

            # if English source needed plural pair repairs, persist it
            if raw_source_data != normalized_source:
                save_json(normalized_source, args.source)
                print(f"Repaired and saved source file: {args.source}")

            # persist projected Russian target
            save_json(synced_target, args.target)
            print(f"Synchronized and saved target file: {args.target}")
        else:
            print(
                "\nDivergence found. Run with '--fix' to apply structural synchronization."
            )
            sys.exit(1)
    else:
        # check if formatting or key ordering differed despite path parity
        if args.fix:
            save_json(normalized_source, args.source)
            save_json(synced_target, args.target)
        print(
            "Locale files are fully synchronized with authoritative source and CLDR plural specifications."
        )


if __name__ == "__main__":
    main()
