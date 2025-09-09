# tests/test_data_pipeline.py
import json
import csv
from pathlib import Path

def test_json_files_exist():
    """Test that JSON files are created."""
    data_dir = Path("data/external")
    json_files = list(data_dir.glob("*.json"))
    assert len(json_files) > 0, "No JSON files found"

def test_csv_files_exist():
    """Test that CSV files are created."""
    data_dir = Path("data/external")
    csv_files = list(data_dir.glob("*.csv"))
    assert len(csv_files) > 0, "No CSV files found"

def test_json_format():
    """Test that JSON files contain valid JSON."""
    data_dir = Path("data/external")
    json_files = list(data_dir.glob("*.json"))

    for json_file in json_files:
        with open(json_file, 'r') as f:
            data = json.load(f)
            assert isinstance(data, list), f"{json_file} should contain a list"
            assert len(data) > 0, f"{json_file} should not be empty"

def test_csv_format():
    """Test that CSV files contain valid CSV."""
    data_dir = Path("data/external")
    csv_files = list(data_dir.glob("*.csv"))

    for csv_file in csv_files:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) > 0, f"{csv_file} should not be empty"

if __name__ == "__main__":
    # Run tests
    test_json_files_exist()
    test_csv_files_exist()
    test_json_format()
    test_csv_format()
    print("All tests passed!")