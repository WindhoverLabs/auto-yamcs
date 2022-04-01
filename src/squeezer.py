import argparse
import subprocess
import os
import logging
from pathlib import Path
import yaml
import sys
import remap_symbols
import msg_def_overrides
import sqlite_utils
import mod_sql

# There does not seem to be a cleaner way of doing this in python when working with git submodules
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../xtce_generator/src')))
sys.path.append(os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../tlm_cmd_merger/src')))
# NOTE:If using Pycharm, add the  "../xtce_generator/src" path to your interpreter,
# otherwise pycharm will think xtce_generator is a directory/package
import xtce_generator
import tlm_cmd_merger

def squeeze_files(elf_files: list, output_path: str, mode: str, verbosity: str):
    subprocess.run(['rm', '-f', output_path])
    subprocess.run(['make', '-C', os.path.join(os.getcwd(), '../juicer')], check=True)

    logging.info('Squeezing files...')
    for file_path in elf_files:
        my_file = Path(file_path)
        if my_file.exists() and my_file.is_file():
            logging.info('Running juicer on {0}'.format(my_file))
            subprocess.run(
                ['../juicer/build/juicer', '--input', file_path, '--mode', mode, '--output', output_path, '-v', verbosity],
                check=True)
        else:
            logging.warning(f'Elf file "{my_file}" does not exist. Revise your configuration file.')


def merge_command_telemetry(yaml_path: str, sqlite_path: str):
    logging.info('Merging commands and telemetry into database.')
    # FIXME: Change the yaml_path to a yaml_dict; this way we avoid parsing the same YAML twice.
    tlm_cmd_merger.merge_all(sqlite_path, yaml_path)


def get_elf_files(yaml_dict: dict):
    elf_files = []

    for module_key in yaml_dict['modules']:
        if 'elf_files' in yaml_dict['modules'][module_key]:
            for elf in yaml_dict['modules'][module_key]['elf_files']:
                elf_files.append(elf)
        if 'modules' in yaml_dict['modules'][module_key]:
            child_elfs = get_elf_files(yaml_dict['modules'][module_key])
            if len(child_elfs)>0:
                elf_files = elf_files + get_elf_files(yaml_dict['modules'][module_key])

    print(elf_files)
    return elf_files

def get_cpu_id(yaml_dict: dict):
    if 'cpu_id' in yaml_dict:
        return yaml_dict['cpu_id']
    return ''

def run_xtce_generator(sqlite_path: str, xtce_yaml: dict, verbosity: str, output_path, cpu_id):
    xtce_generator.generate_xtce(sqlite_path, xtce_yaml, output_path, cpu_id, verbosity)


def read_yaml(yaml_file: str) -> dict:
    yaml_data = yaml.load(open(yaml_file, 'r'),
                          Loader=yaml.FullLoader)
    return yaml_data


def check_version():
    if float(sys.version[0:3]) < float('3.6'):
        logging.error('Python version MUST be 3.6.X or newer. Python version found:{0}'.format(sys.version))
        exit(0)


def remap(database_path: str, remap_yaml_path: str):
    yaml_data = read_yaml(remap_yaml_path)
    logging.info('Remapping synbols...')
    if 'type_remaps' in yaml_data:
        yaml_remaps = read_yaml(remap_yaml_path)['type_remaps']
        remap_symbols.remap_symbols(database_path, yaml_remaps)
    else:
        logging.warning('remap tool was invoked but "type_remaps" configuration does exist on'
                        f'"{remap_yaml_path}". Thus no remapping will be done.')


def run_mod_sql(database_path: str, yaml_path):
    logging.info('Modding sqlite database(manual entries)...')
    mod_sql.mod_sql(database_path, yaml_path)


def __singleton_get_remap(yaml_dict: dict):
    """
    Should be used when user is on "singleton" mode.
    :param yaml_dict:
    :return:
    """
    remaps = {'type_remaps': dict()}

    for module_key in yaml_dict['modules']:
        if 'type_remaps' in yaml_dict['modules'][module_key]:
            for old_symbol, new_symbol in yaml_dict['modules'][module_key]['type_remaps'].items():
                if old_symbol in remaps['type_remaps']:
                    logging.error(f'The {old_symbol} remap appears twice in the config file.'
                                  f'Please review the configuration file.')
                    raise Exception('Duplicate remapping in configuration file.')
                remaps['type_remaps'].update({old_symbol: new_symbol})
        if 'modules' in yaml_dict['modules'][module_key]:
            remaps['type_remaps'].update(__singleton_get_remap(yaml_dict['modules'][module_key])['type_remaps'])

    return remaps


def __inline_get_remaps(yaml_data: dict):
    """
    Should only be used when in "inline" mode.
    :param yaml_data:
    :return:
    """
    out_remaps = dict({'type_remaps': dict()})
    logging.info('Remapping synbols...')
    if 'type_remaps' in yaml_data:
        out_remaps['type_remaps'] = yaml_data['type_remaps']
    else:
        logging.warning('remap tool was invoked but "type_remaps" configuration does exist on'
                        f' configuration file.')

    return out_remaps


# FIXME: I don't like the fact I'm repeating code here that is also on xtce_generator.py. Will revise.
log_level_map = {
    '1': logging.ERROR,
    '2': logging.WARNING,
    '3': logging.INFO,
    '4': logging.DEBUG
}


def set_log_level(log_level: str):
    if log_level == '0':
        for key, level in log_level_map.items():
            logging.disable(level)
    else:
        logging.getLogger().setLevel(log_level_map[log_level])

    logging.getLogger().name = 'squeezer'


def run_msg_def_overrides(yaml_path: str, sqlite_path: str):
    yaml_overrides_dict = read_yaml(yaml_path)
    db_handle = sqlite_utils.Database(sqlite_path)
    logging.info('Processing overrides...')
    msg_def_overrides.process_def_overrides(yaml_overrides_dict, db_handle)


def inline_mode_handler(args: argparse.Namespace):
    logging.info('"inline" mode invoked.')
    yaml_dict = read_yaml(args.inline_yaml_path)
    set_log_level(args.verbosity)

    elfs = get_elf_files(yaml_dict)

    squeeze_files(elfs, args.output_file, args.juicer_mode, args.verbosity)
    merge_command_telemetry(args.inline_yaml_path, args.output_file)

    if args.remap_yaml:
        yaml_remaps_dict = read_yaml(args.remap_yaml)
        yaml_remaps = __inline_get_remaps(yaml_remaps_dict)
        if len(yaml_remaps['type_remaps']) > 0:
            remap_symbols.remap_symbols(args.output_file, yaml_remaps['type_remaps'])
        else:
            logging.warning('No type_remaps configuration found. No remapping was done done.')

    if args.sql_yaml:
        run_mod_sql(args.output_file, args.sql_yaml)

    if args.override_yaml:
        run_msg_def_overrides(args.override_yaml, args.output_file)

    xtce_config_data = read_yaml(args.xtce_config_yaml)
    run_xtce_generator(args.output_file, xtce_config_data, args.verbosity, args.xtce_output_path, None)


def singleton_mode_handler(args: argparse.Namespace):
    """
    The singleton mode allows the user to pass in one YAML file tha combines all YAML files into one.
    This function is invoked when the "singleton" argument is passed in from the command line.
    :param args:
    :return:
    """
    yaml_dict = read_yaml(args.singleton_yaml_path)
    set_log_level(args.verbosity)

    elfs = get_elf_files(yaml_dict)
    
    squeeze_files(elfs, args.output_file, args.juicer_mode, args.verbosity)

    cpu_id = get_cpu_id(yaml_dict)

    yaml_remaps = __singleton_get_remap(yaml_dict)

    if len(yaml_remaps['type_remaps']) > 0:
        remap_symbols.remap_symbols(args.output_file, yaml_remaps['type_remaps'])
    else:
        logging.warning('No type_remaps configuration found. No type_remapping was done done.')

    merge_command_telemetry(args.singleton_yaml_path, args.output_file)
    run_msg_def_overrides(args.singleton_yaml_path, args.output_file)

    if 'xtce_config' in yaml_dict:
        xtce_config_data = yaml_dict['xtce_config']
    else:
        logging.warning(f'The xtce configuration file "{args.singleton_yaml_path}" has no "xtce_config" key.'
                        'No configuration will be applied when generating xtce file.')
        xtce_config_data = None

    run_xtce_generator(args.output_file, xtce_config_data, args.verbosity, args.xtce_output_path, cpu_id)

def parse_cli() -> argparse.Namespace:
    """
    Parses cli arguments.
    :return: The namespace that has all of the arguments that have been parsed.
    """
    parser = argparse.ArgumentParser(add_help=False)

    parent_parser = argparse.ArgumentParser(add_help=False)

    parent_parser.add_argument('--juicer_mode', type=str, default='SQLITE', choices=['SQLITE'],
                               help='The mode which to run juicer on')

    parent_parser.add_argument('--output_file', type=str, default='newdb.sqlite',
                               help='The output file juicer will write to; the database.', required=True)

    parent_parser.add_argument('--verbosity', type=str, default='0', choices=['0', '1', '2', '3', '4'],
                               help='[(0=SILENT), (1=ERRORS), (2=WARNINGS), (3=INFO), (4=DEBUG)]')

    parent_parser.add_argument('--xtce_output_path', type=str, default=None,
                               help='The output path where to write the output XTCE to.')

    subparsers = parser.add_subparsers(
        description='Mode to run squeezer.',
        dest='inline | singleton',
        help='Pass a single YAML or invoke each tool separately.'
    )

    singleton_parser = subparsers.add_parser(
        'singleton',
        help='Run using a single YAML file.',
        parents=[parent_parser],
    )

    inline_parser = subparsers.add_parser(
        'inline',
        help='Run invoking every tool individually. Can provide flexibility in some cases.',
        parents=[parent_parser]
    )
    singleton_parser.set_defaults(func=singleton_mode_handler)
    inline_parser.set_defaults(func=inline_mode_handler)

    inline_parser.add_argument('--inline_yaml_path', type=str, required=True,
                               help='The yaml_path that will be passed to tlm_cmd_merger.py. '
                                    'This script uses this config file '
                                    'as well to know which binary files to pass to juicer')

    inline_parser.add_argument('--xtce_config_yaml', type=str, required=True,
                               help='The yaml file that will be passed to xtce_generator. xtce_generator will use this'
                                    ' to map base containers for telemetry and commands.')

    inline_parser.add_argument('--remap_yaml', type=str, default=None,
                               help='An optional remap configuration file that can be used to remap symbols in the database after'
                                    'it is created.')

    inline_parser.add_argument('--sql_yaml', type=str, default=None,
                               help='An optional config file which can be used to insert extra data into the database after juicer'
                                    'is done parsing.')

    inline_parser.add_argument('--override_yaml', type=str, default=None,
                               help='Optional configuration file to override types in the database. '
                                    'This can be useful for turning "char[SIZE]" tpes into "string" types for'
                                    'a ground system.')

    singleton_parser.add_argument('--singleton_yaml_path', type=str, required=True, help='A single YAML file that '
                                  'has everything auto-yamcs needs.')

    return parser.parse_args()


def main():
    check_version()

    args = parse_cli()

    # FIXME: There has to be a cleaner way of doing this.
    if 'func' in args:
        args.func(args)

    else:
        print('A mode must be passed:{"inline", "singleton"}')


if __name__ == '__main__':
    main()
