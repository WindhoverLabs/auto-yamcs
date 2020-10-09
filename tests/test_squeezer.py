import subprocess
import sys
import os
from pathlib import Path

# There does not seem to be a cleaner way of doing this in python when working with git submodules
sys.path.append(os.path.join(os.getcwd(), '../xtce_generator'))
import squeezer
import sys
from unittest.mock import patch


def test_juicer(monkeypatch):
    """
    Test juicer with "make run-tests"
    :return:
    """
    # FIXME: It might be best to make this directory configuration a fixture to avoid code duplication
    if Path(os.getcwd()).parts[-1] != 'auto-yamcs':
        monkeypatch.chdir("..")

    subprocess.run(['make', '-C', 'juicer', 'run-tests'], check=True)


def test_squeezer(monkeypatch):
    args = ['',
            '--yaml_path',
            'tests/test_combined.yml',
            '--output_file',
            'newdb.sqlite',
            '--xtce_config_yaml',
            'xtce_generator/src/config.yaml', ]

    if Path(os.getcwd()).parts[-1] != 'auto-yamcs':
        monkeypatch.chdir("..")

    with patch.object(sys, 'argv', args):
        squeezer.main()

    # TODO: The correctness of the database should be tested.

    os.remove('newdb.sqlite')
    os.remove('airliner.xml')
