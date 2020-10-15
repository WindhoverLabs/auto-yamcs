import yaml_validator
from unittest.mock import patch
from pathlib import Path
import os


def test_val(monkeypatch):
    # FIXME: This path handling should be a fixture to avoid code duplication.
    if Path(os.getcwd()).parts[-1] != 'tests':
        monkeypatch.chdir("tests")
    assert(yaml_validator.val('test_schema.yml', 'test_yaml.yml') is True)

