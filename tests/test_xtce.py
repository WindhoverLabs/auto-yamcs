import unittest
from unittest.mock import patch

import sys
import os
# There does not seem to be a cleaner way of doing this in python when working with git submodules
sys.path.append(os.path.realpath(os.path.join(os.path.realpath(__file__), '../../src')))
sys.path.append(os.path.realpath(os.path.join(os.path.realpath(__file__), '../../xtce-generator/src')))
import src.squeezer as squeezer
import xtce_generator

class MyTestCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, True)  # add assertion here

def test_xtce_no_cpu_id(monkeypatch, get_tests_path):
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

    monkeypatch.chdir(os.path.join(get_tests_path, '../src'))

    with patch.object(sys, 'argv', args):
        squeezer.main()

    os.remove('cfs.xml')
    # set_log_level(log_level)

    xtce_obj = xtce_generator.XTCEManager("cfs", 'cfs.xml', 'newdb.sqlite', '../tests/data/xtce_config.yaml', None)
    xtce_obj.add_base_types('TestBaseType')
    #
    # logging.info('Adding aggregate types to xtce...')
    # xtce_obj.add_aggregate_types()
    #
    # logging.info('Writing xtce object to file...')
    # xtce_obj.write_to_file(namespace=root_spacesystem)
    #
    # logging.info(f'XTCE file has been written to "{xtce_obj.output_file}"')

    # TODO: The correctness of the database should be tested.

    # os.remove('newdb.sqlite')
    # os.remove('cfs.xml')

if __name__ == '__main__':
    unittest.main()
