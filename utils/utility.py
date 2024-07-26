import json
from config.team import names


def write_json(file_name: str, data: dict|list, mode="w", indent=4):
    with open(f"testing_data/{file_name}.json", mode) as data_file:
        json.dump(data, data_file, indent=indent)
