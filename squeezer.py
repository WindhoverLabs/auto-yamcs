import argparse
import subprocess
import os
from pathlib import Path

file_paths = ['target/exe/airliner',
              'target/exe/cf/apps/CFS_LIB.so',
              'target/exe/cf/apps/CF.so',
              'target/exe/cf/apps/CI.so',
              'target/exe/cf/apps/CS.so',
              'target/exe/cf/apps/DS.so',
              'target/exe/cf/apps/FM.so',
              'target/exe/cf/apps/HK.so',
              'target/exe/cf/apps/HS.so',
              'target/exe/cf/apps/LC.so',
              'target/exe/cf/apps/MD.so',
              'target/exe/cf/apps/MM.so',
              'target/exe/cf/apps/SCH.so',
              'target/exe/cf/apps/SC.so',
              'target/exe/cf/apps/TO.so']


def parse_cli() -> argparse.Namespace:
    """
    Parses cli argyments.
    :return: The namespace that has all of the arguments that have been parsed.
    """
    parser = argparse.ArgumentParser(description='Takes in path to sqlite database.')
    parser.add_argument('--build_dir', type=str, default='airliner',
                        help=' The root directory where the elf files are that will be squeezed with juicer')
    parser.add_argument('--mode', type=str, default='SQLITE', choices=['SQLITE'],
                        help=' The mode which to run juicer on')
    parser.add_argument('--output_file', type=str, default='build/newdb', help='The output file juier will write to.')

    parser.add_argument('--verbosity', type=str, default='4', choices=['1','2','3','4'],
                        help='The verbosity with which to run juicer.')

    parser.add_argument('--yaml_path', type=str, default='4',
                        help='The yaml_path that will be passed to tlm_cmd_merger.py.')

    parser.add_argument('--spacesystem', type=str, default='airliner',
                        help='The name of the root spacesystem of the xtce file. Note that spacesystem is a synonym '
                             'for namespace')

    return parser.parse_args()


def squeeze_files(build_dir: str, output_path: str, mode: str, verbosity: str):
    subprocess.run(["rm", output_path], cwd='./juicer')
    subprocess.run(["make"], cwd='./juicer')

    for path in file_paths:
        file_path = os.path.join(build_dir, path)
        print('file path-->', build_dir)
        my_file = Path(file_path)
        if my_file.exists():
            subprocess.run(['build/juicer', '--input', file_path, '--mode', mode, '--output', output_path,'-v', verbosity],
                            cwd="juicer")


def create_venv():
    subprocess.run(['python3.6', '-m' 'venv', 'venv'])
    subprocess.run(['./venv/bin/pip', 'install', 'six'])
    subprocess.run(['./venv/bin/pip', 'install', 'pyyaml'])


def merge_files(yaml_path: str, sqlite_path: str):
    subprocess.run(['../venv/bin/python', '../tlm_cmd_merger/src/tlm_cmd_merger.py', '--yaml_path',
                    os.path.join('..', yaml_path),
                    '--sqlite_path', sqlite_path], cwd='juicer')


# FIXME: Implement
def generate_xtce(sqlite_path: str):
    pass


def main():
    create_venv()
    args = parse_cli()
    squeeze_files(args.build_dir, args.output_file, args.mode, args.verbosity)
    merge_files(args.yaml_path, args.output_file)


if __name__ == '__main__':
    main()