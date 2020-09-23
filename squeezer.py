import argparse
import subprocess
import os

file_paths = ['cfs/target/exe/airliner',
              'cfs/target/exe/cf/apps/CFS_LIB.so',
              'cfs/target/exe/cf/apps/CF.so',
              'cfs/target/exe/cf/apps/CI.so',
              'cfs/target/exe/cf/apps/CS.so',
              'cfs/target/exe/cf/apps/DS.so',
              'cfs/target/exe/cf/apps/FM.so',
              'cfs/target/exe/cf/apps/HK.so',
              'cfs/target/exe/cf/apps/HS.so',
              'cfs/target/exe/cf/apps/LC.so',
              'cfs/target/exe/cf/apps/MD.so',
              'cfs/target/exe/cf/apps/MM.so',
              'cfs/target/exe/cf/apps/SCH.so',
              'cfs/target/exe/cf/apps/SC.so',
              'cfs/target/exe/cf/apps/TO.so',]


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

    return parser.parse_args()


def squeeze_files(build_dir: str, output_path: str, mode: str, verbosity: str):
    subprocess.run(["rm", "build/new_db.sqlite"], cwd='./juicer')
    subprocess.run(["make"], cwd='./juicer')
    juicer_command = []

    for path in file_paths:
        file_path = os.path.join(build_dir, path)
        juicer_command += 'build/juicer --input'
        subprocess.run(['build/juicer', '--input',file_path, '--mode', mode, '--output', output_path ,'-v', verbosity], cwd="juicer")


def main():
    args = parse_cli()
    squeeze_files(args.build_dir, args.output_file, args.mode, args.verbosity)


if __name__ == '__main__':
    main()