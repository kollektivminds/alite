#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path


def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def collect_paths(data, prefix=""):
    """ Recursively collect JSON keys paths as dot-separated strings """
    paths = set()
    for key, value in data.items():
        current_path = f"{prefix}.{key}" if prefix else key
        paths.add(current_path)
        if isinstance(value, dict):
            paths.update(collect_paths(value, current_path))
    return paths


def merge_keys(source, target):
    """ Recursively merge keys from source into target """
    for key, value in source.items():
        if key not in target:
            target[key] = value# if not isinstance(value, dict) else {}
        elif isinstance(value, dict) and isinstance(target[key], dict):
            merge_keys(value, target[key])
    return target


def main():
    parser = argparse.ArgumentParser(description="Compare or synchronize JSON keys between two files.")
    parser.add_argument("source", type=Path, default="../locales/en/translations.json", nargs='?', help="Source JSON file")
    parser.add_argument("target", type=Path, default="../locales/ru/translations.json", nargs='?', help="Target JSON file")
    parser.add_argument("--fix", action="store_true", help="Fix missing keys by copying from source")

    args = parser.parse_args()

    try:
        source_data = load_json(args.source)
        target_data = load_json(args.target)
    except Exception as e:
        print(f"Error reading files: {e}")
        sys.exit(1)

    source_keys = collect_paths(source_data)
    target_keys = collect_paths(target_data)

    missing_in_target = source_keys - target_keys
    missing_in_source = target_keys - source_keys

    if missing_in_target or missing_in_source:
        print(f"⚠️ Key differences detected between {args.source} and {args.target}")

        if missing_in_target:
            print(f"  Missing in {args.target}:")
            for key in sorted(missing_in_target):
                print(f"    - {key}")

        if missing_in_source:
            print(f"  Missing in {args.source}:")
            for key in sorted(missing_in_source):
                print(f"    - {key}")

        if args.fix:
            print("🔧 Applying --fix: synchronizing missing keys...")
            merge_keys(source_data, target_data)
            merge_keys(target_data, source_data)
            save_json(source_data, args.source)
            save_json(target_data, args.target)
            print("✅ Keys synchronized.")
        else:
            print("❌ Differences detected. Run with --fix to resolve.")
            sys.exit(1)
    else:
        print("✅ No key differences found. Files are synchronized.")


if __name__ == "__main__":
    main()
