import json

input_filename = "/Users/aaron.thompson/code/alite/app/backend/src/alite_backend/words/data/word_cache.json"
output_filename = "/Users/aaron.thompson/code/alite/app/backend/src/alite_backend/words/data/readable_cache.json"

print("Decoding JSON file...")

with open(input_filename, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Number of items in cache: {len(data)}")

with open(output_filename, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(f"Done!")