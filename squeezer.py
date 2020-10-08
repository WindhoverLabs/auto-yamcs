import argparse
import subprocess
import os
import logging
from pathlib import Path
import yaml
import sys
import tlm_cmd_merger.src.tlm_cmd_merger as tlm_cmd_merger


def squeeze_files(elf_files: list, output_path: str, mode: str, verbosity: str):
    subprocess.run(['rm', output_path])
    subprocess.run(['make', '-C', 'juicer'], check=True)

    for file_path in elf_files:
        my_file = Path(file_path)
        if my_file.exists() and my_file.is_file():
            print('Running juicer on {0}'.format(my_file))
            subprocess.run(
                ['juicer/build/juicer', '--input', file_path, '--mode', mode, '--output', output_path, '-v', verbosity],
                check=True)


def merge_files(yaml_path: str, sqlite_path: str):
    subprocess.run(['python3', '../tlm_cmd_merger/src/tlm_cmd_merger.py', '--yaml_path',
                    os.path.join('..', yaml_path),
                    '--sqlite_path', sqlite_path], cwd='juicer')


def get_elf_files(yaml_dict: dict):
    elf_files = []
    elf_files += yaml_dict['core']['elf_files']
    for module_key in yaml_dict['modules']:
        for elf in yaml_dict['modules'][module_key]['elf_files']:
            elf_files.append(elf)

    return elf_files


# FIXME: Implement
def generate_xtce(sqlite_path: str):
    pass


def parse_cli() -> argparse.Namespace:
    """
    Parses cli argyments.
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

    parser.add_argument('--spacesystem', type=str, default='airliner',
                        help='The name of the root spacesystem of the xtce file. Note that spacesystem is a synonym '
                             'for namespace')

    return parser.parse_args()


def read_yaml(yaml_file: str) -> dict:
    yaml_data = yaml.load(open(yaml_file, 'r'),
                          Loader=yaml.FullLoader)
    return yaml_data


def check_version():
    if sys.version[0:3] < '3.6':
        logging.error('Python version MUST be 3.6.X or newer. Python version found:{0}'.format(sys.version))
        exit(0)


def main():
    check_version()
    args = parse_cli()
    yaml_dict = read_yaml(args.yaml_path)

    elfs = get_elf_files(yaml_dict)

    squeeze_files(elfs, args.output_file, args.mode, args.verbosity)
    # merge_files(args.yaml_path, args.output_file)


if __name__ == '__main__':
    main()
