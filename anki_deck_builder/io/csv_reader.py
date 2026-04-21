import csv


def load_rows(csv_file: str) -> list[dict]:
    with open(csv_file, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
