import json
import sys
import argparse

def find_deep_differences(v1, v2, path=""):
    """Recursively traverses ALL nesting levels (dicts, lists, primitives)

    to isolate differences.
    """
    diffs = []

    # Case 1: Both are Dictionaries
    if isinstance(v1, dict) and isinstance(v2, dict):
        # Look for keys in the first dictionary
        for k in v1:
            current_path = f"{path}.{k}" if path else k
            if k not in v2:
                diffs.append(
                    f"  ❌ Missing in second structure:\n    {current_path}: {repr(v1[k])}"
                )
            else:
                diffs.extend(find_deep_differences(v1[k], v2[k], current_path))

        # Look for keys missing in the first dictionary
        for k in v2:
            current_path = f"{path}.{k}" if path else k
            if k not in v1:
                diffs.append(
                    f"  ❌ Missing in first structure:\n    {current_path}: {repr(v2[k])}"
                )

    # Case 2: Both are Lists/Arrays (Traverse by index)
    elif isinstance(v1, list) and isinstance(v2, list):
        len1, len2 = len(v1), len(v2)
        max_len = max(len1, len2)

        for idx in range(max_len):
            current_path = f"{path}[{idx}]"

            if idx >= len1:
                diffs.append(
                    f"  ❌ Array Element Missing in first structure:\n    {current_path}: {repr(v2[idx])}"
                )
            elif idx >= len2:
                diffs.append(
                    f"  ❌ Array Element Missing in second structure:\n    {current_path}: {repr(v1[idx])}"
                )
            else:
                diffs.extend(find_deep_differences(v1[idx], v2[idx], current_path))

    # Case 3: Values differ (Terminal Leaf Node / Primitive values)
    elif v1 != v2:
        diffs.append(
            f"  ⚡ Value Mismatch at '{path}':\n    - First:  {repr(v1)}\n    - Second: {repr(v2)}"
        )

    return diffs


def check_and_clean_json(file_path, delete_mode, output_path=None):
    conflicting_keys = {}

    def tracking_hook(pairs):
        seen = {}
        unique_pairs = []

        for key, value in pairs:
            if key in seen:
                if seen[key] != value:
                    # Run the absolute deep traversal check on the structures
                    diffs = find_deep_differences(seen[key], value, path=key)
                    if diffs:
                        # Merge diffs if the root key duplicates multiple times
                        if key in conflicting_keys:
                            conflicting_keys[key].extend(diffs)
                        else:
                            conflicting_keys[key] = diffs

                if delete_mode:
                    continue
            else:
                seen[key] = value

            unique_pairs.append((key, value))
        return dict(unique_pairs)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_data = f.read()

        cleaned_data = json.loads(raw_data, object_pairs_hook=tracking_hook)

        # --- OUTPUT ONLY DIFFERENCES ---
        if conflicting_keys:
            for root_key, diff_list in conflicting_keys.items():
                print(f"\n[Duplicate Root Key: '{root_key}']")
                # Remove exact duplicate diff prints if the parser hits them twice
                for diff in dict.fromkeys(diff_list):
                    print(diff)
        else:
            print("No conflicting duplicate nested values found.")

        if delete_mode:
            out_file = output_path if output_path else file_path
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(cleaned_data, f, indent=4, ensure_ascii=False)
            print(
                f"\n🧹 Cleaned JSON saved to '{out_file}' (kept first occurrence)."
            )

    except FileNotFoundError:
        print(f"Error: The file '{file_path}' does not exist.")
    except json.JSONDecodeError as e:
        print(f"Syntax Error: The file is not valid JSON ({e}).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Infinite depth JSON duplicate checker."
    )
    parser.add_argument("file", help="Path to the JSON file.")
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete duplicates, keeping first seen item.",
    )
    parser.add_argument("--out", help="Optional output file path.")

    args = parser.parse_args()
    check_and_clean_json(args.file, args.delete, args.out)