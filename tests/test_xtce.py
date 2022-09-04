import unittest
from pathlib import Path
from unittest.mock import patch

import sys
import os

# There does not seem to be a cleaner way of doing this in python when working with git submodules
from xtce_generator.src.xtce.xtce_msg_parser import XTCEParser

sys.path.append(os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../')))
sys.path.append(os.path.realpath(os.path.join(os.path.realpath(__file__), '../../xtce-generator/src')))
import src.squeezer as squeezer
import xtce_generator.src.xtce.xtce_generator as xtce_generator


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

    with patch.object(sys, 'argv', args):
        monkeypatch.chdir(os.path.join(get_tests_path, '../src'))

        args = squeezer.parse_cli()

        yaml_dict = squeezer.read_yaml(args.inline_yaml_path)
        squeezer.set_log_level(args.verbosity)

        elfs = squeezer.get_elf_files(yaml_dict)

        squeezer.squeeze_files(elfs, args.output_file, args.juicer_mode, args.verbosity)
        squeezer.merge_command_telemetry(args.inline_yaml_path, args.output_file)

        if args.remap_yaml:
            yaml_remaps_dict = squeezer.read_yaml(args.remap_yaml)
            yaml_remaps = squeezer.__inline_get_remaps(yaml_remaps_dict)
            if len(yaml_remaps['type_remaps']) > 0:
                squeezer.remap_symbols.remap_symbols(args.output_file, yaml_remaps['type_remaps'])
            else:
                squeezer.logging.warning('No type_remaps configuration found. No remapping was done done.')

        if args.sql_yaml:
            squeezer.run_mod_sql(args.output_file, args.sql_yaml)

        if args.override_yaml:
            squeezer.run_msg_def_overrides(args.override_yaml, args.output_file)

        xtce_obj = xtce_generator.XTCEManager("cfs", 'cfs.xml', 'newdb.sqlite', '../tests/data/xtce_config.yaml', None)
        xtce_obj.add_base_types()

        assert xtce_obj.root is not None
        assert xtce_obj.root.get_SpaceSystem is not None
        assert xtce_obj['BaseType'] is not None
        assert xtce_obj.BASE_TYPE_NAMESPACE == 'BaseType'
        assert xtce_obj['BaseType'].get_name() == 'BaseType'
        assert xtce_obj['BaseType'].get_TelemetryMetaData() is not None

        assert xtce_obj['BaseType'].get_TelemetryMetaData().get_ParameterTypeSet() is not None
        assert xtce_obj['BaseType'].get_CommandMetaData().get_ArgumentTypeSet() is not None

        #
        # logging.info('Adding aggregate types to xtce...')
        # xtce_obj.add_aggregate_types()
        #
        # logging.info('Writing xtce object to file...')
        # xtce_obj.write_to_file(namespace=root_spacesystem)
        #
        # logging.info(f'XTCE file has been written to "{xtce_obj.output_file}"')
        #
        # # TODO: The correctness of the database should be tested.
        # os.remove('newdb.sqlite')
        # os.remove('cfs.xml')


def test_xtce_msg_parser(monkeypatch, get_data_path):
    monkeypatch.chdir(get_data_path)
    # FIXME:Implement tests for new parser
    ppd = Path('./mdb/ppd.xml').resolve()
    cpd = Path('./mdb/cpd.xml').resolve()
    simlink = Path('./mdb/simlink.xml').resolve()
    ccscds = Path('./mdb/cfs-ccsds.xml').resolve()

    parser = XTCEParser([str(ppd), str(cpd), str(simlink)], str(ccscds), "registry.yaml")
    tlm_map = parser.get_msg_ids_at('/cfs/cpd/core/cfe/cfe_es')

    assert tlm_map is not None
    assert tlm_map['CFE_ES_HK_TLM_MID']['msgID'] == 2575


if __name__ == '__main__':
    unittest.main()
