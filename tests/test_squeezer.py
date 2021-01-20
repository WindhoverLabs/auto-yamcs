import subprocess
import sys
import os

# There does not seem to be a cleaner way of doing this in python when working with git submodules
sys.path.append(os.path.realpath(os.path.join(os.path.realpath(__file__), '../../src')))
sys.path.append(os.path.realpath(os.path.join(os.path.realpath(__file__), '../../xtce-workspace/src')))
# FIXME: This path busisness is getting out of hand; I have opened an issue on Github:https://github.com/WindhoverLabs/auto-yamcs/issues/17


import src.squeezer as squeezer
import sys
from unittest.mock import patch

print('cwd:', os.getcwd())
# exit()

def test_juicer(monkeypatch, get_tests_path):
    """
    Test juicer with "make run-tests"
    :return:
    """
    monkeypatch.chdir(os.path.join(get_tests_path, '../src'))
    print('test path:',os.path.join(get_tests_path, '../src'))
    subprocess.run(['make', '-C', '../juicer', 'run-tests'], check=True)


def test_squeezer(monkeypatch, get_tests_path):

    args = ['',
            'inline',
            '--inline_yaml_path',
            '../tests/data/test_combined.yml',
            '--output_file',
            'newdb.sqlite',
            '--xtce_config_yaml',
            '../tests/data/xtce_config.yaml',
            '--xtce_output_path',
            'cfs.xml',
            '--verbosity',
            '0']

    print('get_tests_path', get_tests_path)

    monkeypatch.chdir(os.path.join(get_tests_path, '../src'))

    with patch.object(sys, 'argv', args):
        squeezer.main()

    # TODO: The correctness of the database should be tested.

    os.remove('newdb.sqlite')
    os.remove('cfs.xml')
