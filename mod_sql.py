import sqlite_utils
import argparse
import sys
import logging
import yaml

def parse_cli(args: list = sys.argv) -> argparse.Namespace:
    """
    Parses cli argyments.
    :return: The namespace that has all of the arguments that have been parsed.
    """
    parser = argparse.ArgumentParser(description='Takes in path to sqlite database.')

    parser.add_argument('--yaml_path', type=str, required=True,
                        help=' The path to the yaml file')

    parser.add_argument('--sqlite_path', type=str, required=True,
                        help=' The path to the sqlite database.')

    return parser.parse_args()


def read_yaml(yaml_file: str) -> dict:
    yaml_data = yaml.load(open(yaml_file, 'r'),
                          Loader=yaml.FullLoader)
    return yaml_data


def main():
    args = parse_cli(sys.argv)
    db = sqlite_utils.Database(args.sqlite_path)

    yaml_dict = read_yaml(args.yaml_path)

    for table in yaml_dict['tables']:
        for data in yaml_dict['tables'][table]:
            if table == 'symbols':
                print(f'elf-->{data["elf"]}')
                for row in db['elfs'].rows_where(f'name={data["elf"]}'):
                    print(f'row:-->{row}')
            #     data["elf"] = elf_key
            # db[table].insert(data)

    # db['elfs'].insert({'name': 'a_new_elf',
    #                    'checksum': 0,
    #                   'little_endian': 0})
    logging.info('Wrote data to the database.')


if __name__ == '__main__':
    main()