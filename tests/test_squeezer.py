import pytest
import subprocess
import sys
import os

# There does not seem to be a cleaner way of doing this in python when working with git submodules
sys.path.append(os.path.join(os.getcwd(), '../xtce_generator'))
import squeezer
import sys
from unittest.mock import patch


def test_juicer():
    """
    Test juicer with "make run-tests"
    :return:
    """
    subprocess.run(['make', '-C', '../juicer', 'run-tests'], check=True)


def test_squeezer(monkeypatch):
    args = ['',
            '--yaml_path',
            'tlm_cmd_merger/src/combined.yml',
            '--output_file',
            'newdb.sqlite',
            '--verbosity',
            '4',
            '--remap_yaml',
            'config_remap.yaml',
            '--xtce_config_yaml',
            'xtce_generator/src/config.yaml', ]
    monkeypatch.chdir("..")
    with patch.object(sys, 'argv', args):
        squeezer.main()
