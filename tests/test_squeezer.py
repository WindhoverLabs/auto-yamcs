import subprocess
import sys
import os

# There does not seem to be a cleaner way of doing this in python when working with git submodules
sys.path.append(os.path.join(os.getcwd(), '../xtce_generator'))
import squeezer
import sys
from unittest.mock import patch


def test_juicer(monkeypatch, get_tests_path):
    """
    Test juicer with "make run-tests"
    :return:
    """
    monkeypatch.chdir(os.path.join(get_tests_path, '..'))
    subprocess.run(['make', '-C', 'juicer', 'run-tests'], check=True)


def test_squeezer(monkeypatch, get_tests_path):
    args = ['',
            'inline',
            '--yaml_path',
            'tests/data/test_combined.yml',
            '--output_file',
            'newdb.sqlite',
            '--xtce_config_yaml',
            'tests/data/xtce_config.yaml',
            '--xtce_output_path',
            'cfs.xml']

    monkeypatch.chdir(os.path.join(get_tests_path, '..'))

    with patch.object(sys, 'argv', args):
        squeezer.main()

    # TODO: The correctness of the database should be tested.

    os.remove('newdb.sqlite')
    os.remove('cfs.xml')
