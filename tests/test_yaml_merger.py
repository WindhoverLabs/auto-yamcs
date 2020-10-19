import os
import yaml_merger
import sys
from unittest.mock import patch


def test_yaml_merger(monkeypatch, get_data_path):
    args = ['',
            '--source',
            'ying.yml',
            '--destination',
            'yang.yml']

    monkeypatch.chdir(get_data_path)

    with patch.object(sys, 'argv', args):
        yaml_merger.main()
