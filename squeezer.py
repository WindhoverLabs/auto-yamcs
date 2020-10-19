import argparse
import subprocess
import os
import logging
from pathlib import Path
import yaml
import tlm_cmd_merger.src.tlm_cmd_merger as tlm_cmd_merger
import sys
import remap_symbols
# There does not seem to be a cleaner way of doing this in python when working with git submodules
sys.path.append(os.path.join(os.getcwd(), 'xtce_generator'))

import xtce_generator.src.xtce_generator as xtce_generator

import mod_sql

def squeeze_files(elf_files: list, output_path: str, mode: str, verbosity: str):
    subprocess.run(['rm', output_path])
    subprocess.run(['make', '-C', os.path.join(os.getcwd(), 'juicer')], check=True)

    for file_path in elf_files:
        my_file = Path(file_path)
        if my_file.exists() and my_file.is_file():
            print('Running juicer on {0}'.format(my_file))
            subprocess.run(
                ['juicer/build/juicer', '--input', file_path, '--mode', mode, '--output', output_path, '-v', verbosity],
                check=True)


def merge_files(yaml_path: str, sqlite_path: str):
    tlm_cmd_merger.merge_all(sqlite_path, yaml_path)


def get_elf_files(yaml_dict: dict):
    elf_files = []

    # In our airliner setup, we have a special key called "core"
    if 'core' in yaml_dict:
        elf_files += yaml_dict['core']['elf_files']

    for module_key in yaml_dict['modules']:
        for elf in yaml_dict['modules'][module_key]['elf_files']:
            elf_files.append(elf)

    return elf_files


def run_xtce_generator(sqlite_path: str, xtce_yaml: str, root_spacesystem: str):
    xtce_generator.generate_xtce(sqlite_path, xtce_yaml, root_spacesystem)


def parse_cli() -> argparse.Namespace:
    """
    Parses cli arguments.
    :return: The namespace that has all of the arguments that have been parsed.
    """
    parser = argparse.ArgumentParser(description='Takes in path to sqlite database.')

    parser.add_argument('--mode', type=str, default='SQLITE', choices=['SQLITE'],
                        help=' The mode which to run juicer on')
    parser.add_argument('--output_file', type=str, default='newdb.sqlite', help='The output file juier will write to.')

    parser.add_argument('--verbosity', type=str, default='1', choices=['1', '2', ' 3', '4'],
                        help='The verbosity with which to run juicer.')

    parser.add_argument('--yaml_path', type=str, required=True,
                        help='The yaml_path that will be passed to tlm_cmd_merger.py. This script uses this config file'
                             ' as well to know which binary files to pass to juicer')

    parser.add_argument('--xtce_config_yaml', type=str, required=True,
                        help='The yaml file that will be passed to xtce_generator. xtce_generator will use this'
                             ' to map base containers for telemetry and commands.')

    parser.add_argument('--remap_yaml', type=str, default=None,
                        help='An optional remap configuration file that can be used to remap symbols in the database after'
                             'it is created.')

    parser.add_argument('--sql_yaml', type=str, default=None,
                        help='An optional config file which can be used to insert extra data into the database after juicer'
                             'is done parsing.')

    parser.add_argument('--spacesystem', type=str, default='airliner',
                        help='The name of the root spacesystem of the xtce file. Note that spacesystem is a synonym '
                             'for namespace. The name of this spacesystem is also used as a file name in the form of'
                             '"spacesystem.xml".')

    return parser.parse_args()


def read_yaml(yaml_file: str) -> dict:
    yaml_data = yaml.load(open(yaml_file, 'r'),
                          Loader=yaml.FullLoader)
    return yaml_data


def check_version():
    if sys.version[0:3] < '3.6':
        logging.error('Python version MUST be 3.6.X or newer. Python version found:{0}'.format(sys.version))
        exit(0)


def remap(database_path: str, remap_yaml_path):
    remap_symbols.remap_symbols(database_path, remap_yaml_path)


def run_mod_sql(database_path: str, yaml_path):
    mod_sql.mod_sql(database_path, yaml_path)


def main():
    check_version()
    args = parse_cli()
    yaml_dict = read_yaml(args.yaml_path)

    elfs = get_elf_files(yaml_dict)

    squeeze_files(elfs, args.output_file, args.mode, args.verbosity)
    merge_files(args.yaml_path, args.output_file)

    if args.remap_yaml:
        remap(args.output_file, args.remap_yaml)

    if args.sql_yaml:
        run_mod_sql(args.output_file, args.sql_yaml)

    run_xtce_generator(args.output_file, args.xtce_config_yaml, args.spacesystem)


if __name__ == '__main__':
    main()
